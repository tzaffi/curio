import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    OpenAIError,
)

from curio.llm_caller.auth import (
    OpenAiApiAuthConfig,
    SecretStore,
    resolve_openai_api_key,
)
from curio.llm_caller.models import (
    JsonObject,
    JsonValue,
    LlmAuthError,
    LlmCapability,
    LlmInvalidOutputError,
    LlmMessage,
    LlmMessageRole,
    LlmRejectedRequestError,
    LlmRequest,
    LlmResponse,
    LlmSchemaValidationError,
    LlmTimeoutError,
    ProviderName,
)
from curio.llm_caller.providers import (
    ProviderCallTiming,
    ProviderClientBase,
    ProviderClientConfig,
    build_json_llm_response,
    build_provider_usage,
    measure_provider_call,
)

OPENAI_API_CAPABILITIES = (
    LlmCapability.TEXT_GENERATION,
    LlmCapability.JSON_SCHEMA_OUTPUT,
    LlmCapability.TOKEN_USAGE,
    LlmCapability.CACHED_INPUT_USAGE,
    LlmCapability.REASONING_TOKEN_USAGE,
)


class OpenAiReasoningEffort(StrEnum):
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class OpenAiTextVerbosity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class OpenAiResponsesConfig:
    temperature: float | int | None = None
    reasoning_effort: OpenAiReasoningEffort | str | None = None
    max_output_tokens: int | None = None
    text_verbosity: OpenAiTextVerbosity | str | None = None

    def __post_init__(self) -> None:
        _require_optional_temperature(self.temperature, "temperature")
        object.__setattr__(
            self,
            "reasoning_effort",
            _coerce_optional_str_enum(self.reasoning_effort, "reasoning_effort", OpenAiReasoningEffort),
        )
        _require_optional_positive_int(self.max_output_tokens, "max_output_tokens")
        object.__setattr__(
            self,
            "text_verbosity",
            _coerce_optional_str_enum(self.text_verbosity, "text_verbosity", OpenAiTextVerbosity),
        )


@dataclass(frozen=True, slots=True)
class OpenAiApiCallResult:
    payload: Mapping[str, JsonValue]
    timing: ProviderCallTiming

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(_require_mapping(self.payload, "payload")))


class OpenAiApiTransport(Protocol):
    def create_response(
        self,
        request_payload: Mapping[str, JsonValue],
        *,
        api_key: str,
        auth_config: OpenAiApiAuthConfig,
        timeout_seconds: int,
    ) -> OpenAiApiCallResult: ...


class SdkOpenAiApiTransport:
    def create_response(
        self,
        request_payload: Mapping[str, JsonValue],
        *,
        api_key: str,
        auth_config: OpenAiApiAuthConfig,
        timeout_seconds: int,
    ) -> OpenAiApiCallResult:
        try:
            client = OpenAI(
                api_key=api_key,
                organization=auth_config.organization,
                project=auth_config.project,
                timeout=timeout_seconds,
                max_retries=0,
            )
            response, timing = measure_provider_call(
                lambda: client.responses.create(
                    **dict(request_payload),
                    timeout=timeout_seconds,
                )
            )
        except APITimeoutError as exc:
            raise LlmTimeoutError("openai_api request timed out") from exc
        except APIConnectionError as exc:
            raise LlmRejectedRequestError("openai_api connection failed") from exc
        except APIStatusError as exc:
            if exc.status_code in {401, 403}:
                raise LlmAuthError("openai_api authentication failed") from exc
            raise LlmRejectedRequestError("openai_api request failed") from exc
        except OpenAIError as exc:
            raise LlmRejectedRequestError("openai_api request failed") from exc
        return OpenAiApiCallResult(payload=_response_to_mapping(response), timing=timing)


class OpenAiApiClient(ProviderClientBase):
    def __init__(
        self,
        *,
        transport: OpenAiApiTransport,
        auth_config: OpenAiApiAuthConfig,
        secret_store: SecretStore,
        model: str,
        timeout_seconds: int,
        responses_config: OpenAiResponsesConfig | None = None,
    ) -> None:
        super().__init__(
            ProviderClientConfig(
                provider=ProviderName.OPENAI_API,
                capabilities=OPENAI_API_CAPABILITIES,
            )
        )
        self.transport = transport
        self.auth_config = auth_config
        self.secret_store = secret_store
        self.model = _require_config_string(model, "model")
        self.timeout_seconds = _require_positive_int(timeout_seconds, "timeout_seconds")
        self.responses_config = OpenAiResponsesConfig() if responses_config is None else responses_config

    def complete_after_capability_check(self, request: LlmRequest) -> LlmResponse:
        api_key = resolve_openai_api_key(self.auth_config, self.secret_store)
        request_payload = build_openai_response_request(
            request,
            model=self.model,
            responses_config=self.responses_config,
        )
        call_result = self._create_response(
            request_payload,
            api_key=api_key,
            timeout_seconds=self.timeout_seconds,
        )
        output_value = parse_openai_response_output(call_result.payload)
        _validate_output_schema(request, output_value)
        return build_openai_llm_response(
            request,
            call_result.payload,
            call_result.timing,
            model=self.model,
            output_value=output_value,
        )

    def _create_response(
        self,
        request_payload: Mapping[str, JsonValue],
        *,
        api_key: str,
        timeout_seconds: int,
    ) -> OpenAiApiCallResult:
        try:
            return self.transport.create_response(
                request_payload,
                api_key=api_key,
                auth_config=self.auth_config,
                timeout_seconds=timeout_seconds,
            )
        except TimeoutError as exc:
            raise LlmTimeoutError("openai_api request timed out") from exc


def build_openai_response_request(
    request: LlmRequest,
    *,
    model: str,
    responses_config: OpenAiResponsesConfig | None = None,
) -> JsonObject:
    _require_config_string(model, "model")
    config = OpenAiResponsesConfig() if responses_config is None else responses_config
    text_config: JsonObject = {
        "format": {
            "type": "json_schema",
            "name": request.output.name,
            "schema": dict(request.output.schema),
            "strict": request.output.strict,
        }
    }
    if config.text_verbosity is not None:
        text_verbosity = cast(OpenAiTextVerbosity, config.text_verbosity)
        text_config["verbosity"] = text_verbosity.value
    payload: JsonObject = {
        "model": model,
        "instructions": request.instructions,
        "input": [_message_to_input(message) for message in request.input],
        "text": text_config,
        "metadata": {
            "curio_request_id": request.request_id,
            "curio_workflow": request.workflow,
        },
    }
    if config.temperature is not None:
        payload["temperature"] = config.temperature
    if config.max_output_tokens is not None:
        payload["max_output_tokens"] = config.max_output_tokens
    if config.reasoning_effort is not None:
        reasoning_effort = cast(OpenAiReasoningEffort, config.reasoning_effort)
        payload["reasoning"] = {"effort": reasoning_effort.value}
    return payload


def parse_openai_response_output(payload: Mapping[str, JsonValue]) -> JsonValue:
    response = _require_mapping(payload, "response")
    status = response.get("status")
    if status is not None and status != "completed":
        raise LlmRejectedRequestError("openai_api response was not completed")
    for item in _require_list(response.get("output"), "output"):
        item_payload = _require_mapping(item, "output item")
        if item_payload.get("type") != "message":
            continue
        for content in _require_list(item_payload.get("content"), "content"):
            content_payload = _require_mapping(content, "content item")
            if content_payload.get("type") == "output_text":
                return _parse_output_text(_require_string(content_payload.get("text"), "output text"))
    raise LlmInvalidOutputError("openai_api response did not include output_text")


def build_openai_llm_response(
    request: LlmRequest,
    payload: Mapping[str, JsonValue],
    timing: ProviderCallTiming,
    *,
    model: str,
    output_value: JsonValue,
) -> LlmResponse:
    usage_payload = _optional_mapping(payload.get("usage"))
    usage = build_provider_usage(
        timing,
        input_tokens=_optional_non_negative_number(_usage_field(usage_payload, "input_tokens"), "input_tokens"),
        cached_input_tokens=_optional_non_negative_number(
            _nested_usage_field(usage_payload, "input_tokens_details", "cached_tokens"),
            "cached_input_tokens",
        ),
        output_tokens=_optional_non_negative_number(_usage_field(usage_payload, "output_tokens"), "output_tokens"),
        reasoning_tokens=_optional_non_negative_number(
            _nested_usage_field(usage_payload, "output_tokens_details", "reasoning_tokens"),
            "reasoning_tokens",
        ),
        total_tokens=_optional_non_negative_number(_usage_field(usage_payload, "total_tokens"), "total_tokens"),
        metered_objects=(),
        thinking_seconds=None,
    )
    return build_json_llm_response(
        request,
        provider=ProviderName.OPENAI_API,
        model=_optional_string(payload.get("model")) or model,
        output_value=output_value,
        usage=usage,
    )


def _message_to_input(message: LlmMessage) -> JsonObject:
    role = cast(LlmMessageRole, message.role)
    return {
        "role": role.value,
        "content": [{"type": "input_text", "text": part.text} for part in message.content],
    }


def _validate_output_schema(request: LlmRequest, output_value: JsonValue) -> None:
    validator = Draft202012Validator(dict(request.output.schema), format_checker=FormatChecker())
    try:
        validator.validate(output_value)
    except JsonSchemaLibraryError as exc:
        raise LlmSchemaValidationError("openai_api output did not match requested schema") from exc


def _parse_output_text(value: str) -> JsonValue:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise LlmInvalidOutputError("openai_api output_text is not valid JSON") from exc


def _response_to_mapping(response: object) -> Mapping[str, JsonValue]:
    if isinstance(response, Mapping):
        return cast(Mapping[str, JsonValue], response)
    model_dump = getattr(response, "model_dump", None)
    if callable(model_dump):
        return cast(Mapping[str, JsonValue], model_dump(mode="json"))
    to_dict = getattr(response, "to_dict", None)
    if callable(to_dict):
        return cast(Mapping[str, JsonValue], to_dict())
    raise LlmInvalidOutputError("openai_api SDK response is not serializable")


def _usage_field(usage_payload: Mapping[str, JsonValue] | None, name: str) -> object:
    if usage_payload is None:
        return None
    return usage_payload.get(name)


def _nested_usage_field(usage_payload: Mapping[str, JsonValue] | None, object_name: str, field_name: str) -> object:
    if usage_payload is None:
        return None
    nested = _optional_mapping(usage_payload.get(object_name))
    if nested is None:
        return None
    return nested.get(field_name)


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise LlmInvalidOutputError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _optional_mapping(value: object) -> Mapping[str, JsonValue] | None:
    if value is None:
        return None
    return _require_mapping(value, "field")


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise LlmInvalidOutputError(f"{field_name} must be a list")
    return cast(list[object], value)


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise LlmInvalidOutputError(f"{field_name} must be a string")
    if not value.strip():
        raise LlmInvalidOutputError(f"{field_name} must not be empty")
    return value


def _require_config_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _coerce_optional_str_enum[StrEnumT: StrEnum](
    value: object,
    field_name: str,
    enum_type: type[StrEnumT],
) -> StrEnumT | None:
    if value is None:
        return None
    if isinstance(value, enum_type):
        return value
    value = _require_config_string(value, field_name)
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed_values = ", ".join(member.value for member in enum_type)
        raise ValueError(f"{field_name} must be one of: {allowed_values}") from exc


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_optional_positive_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return _require_positive_int(value, field_name)


def _require_optional_temperature(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number between 0 and 2")
    if not 0 <= value <= 2:
        raise ValueError(f"{field_name} must be a number between 0 and 2")
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return _require_string(value, "string field")


def _optional_non_negative_number(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise LlmInvalidOutputError(f"{field_name} must be a non-negative number")
    if value < 0:
        raise LlmInvalidOutputError(f"{field_name} must be a non-negative number")
    return value
