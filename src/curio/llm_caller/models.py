from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, cast

from curio.schemas import SchemaName, validate_json

JsonObject = dict[str, Any]
JsonValue = Any

LLM_REQUEST_VERSION = "curio-llm-request.v1"
LLM_RESPONSE_VERSION = "curio-llm-response.v1"


class ProviderName(StrEnum):
    CODEX_CLI = "codex_cli"
    OPENAI_API = "openai_api"


class LlmCapability(StrEnum):
    TEXT_GENERATION = "text_generation"
    JSON_SCHEMA_OUTPUT = "json_schema_output"
    TOKEN_USAGE = "token_usage"
    CACHED_INPUT_USAGE = "cached_input_usage"
    REASONING_TOKEN_USAGE = "reasoning_token_usage"
    THINKING_TIME = "thinking_time"
    SUBPROCESS = "subprocess"


class LlmMessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LlmStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LlmCallerError(Exception):
    pass


class LlmConfigurationError(LlmCallerError):
    pass


class LlmProviderNotFoundError(LlmCallerError):
    pass


class LlmAuthError(LlmCallerError):
    pass


class LlmTimeoutError(LlmCallerError):
    pass


class LlmRejectedRequestError(LlmCallerError):
    pass


class LlmInvalidOutputError(LlmCallerError):
    pass


class LlmSchemaValidationError(LlmInvalidOutputError):
    pass


class UnsupportedCapabilityError(LlmCallerError):
    def __init__(
        self,
        required: Sequence[LlmCapability | str],
        available: Sequence[LlmCapability | str],
    ) -> None:
        self.required = _coerce_capabilities(required)
        self.available = _coerce_capabilities(available)
        missing = tuple(capability for capability in self.required if capability not in self.available)
        self.missing = missing
        detail = ", ".join(capability.value for capability in missing) or "none"
        super().__init__(f"provider does not support required capability: {detail}")


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_non_negative_number(value: object, field_name: str) -> float | int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a non-negative number")
    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative number")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_optional_non_negative_number(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    return _require_non_negative_number(value, field_name)


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return cast(list[object], value)


def _require_field(payload: Mapping[str, JsonValue], field_name: str) -> JsonValue:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    return payload[field_name]


def _coerce_capabilities(values: Sequence[LlmCapability | str]) -> tuple[LlmCapability, ...]:
    capabilities = tuple(LlmCapability(value) for value in values)
    if len(capabilities) != len(set(capabilities)):
        raise ValueError("capabilities must be unique")
    return capabilities


def _coerce_warnings(values: Sequence[str]) -> tuple[str, ...]:
    warnings = tuple(values)
    for warning in warnings:
        _require_string(warning, "warning")
    if len(warnings) != len(set(warnings)):
        raise ValueError("warnings must be unique")
    return warnings


@dataclass(frozen=True, slots=True)
class TextContentPart:
    text: str

    def __post_init__(self) -> None:
        _require_string(self.text, "text")

    @classmethod
    def from_json(cls, value: object) -> "TextContentPart":
        payload = _require_mapping(value, "content part")
        part_type = _require_string(_require_field(payload, "type"), "type")
        if part_type != "text":
            raise ValueError("type must be text")
        return cls(text=_require_string(_require_field(payload, "text"), "text"))

    def to_json(self) -> JsonObject:
        return {"type": "text", "text": self.text}


@dataclass(frozen=True, slots=True)
class LlmMessage:
    role: LlmMessageRole | str
    content: Sequence[TextContentPart]

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", LlmMessageRole(self.role))
        content = tuple(self.content)
        if not content:
            raise ValueError("content must not be empty")
        object.__setattr__(self, "content", content)

    @classmethod
    def from_json(cls, value: object) -> "LlmMessage":
        payload = _require_mapping(value, "message")
        return cls(
            role=_require_string(_require_field(payload, "role"), "role"),
            content=[
                TextContentPart.from_json(part)
                for part in _require_list(_require_field(payload, "content"), "content")
            ],
        )

    def to_json(self) -> JsonObject:
        role = cast(LlmMessageRole, self.role)
        return {
            "role": role.value,
            "content": [part.to_json() for part in self.content],
        }


@dataclass(frozen=True, slots=True)
class JsonSchemaOutput:
    name: str
    schema: Mapping[str, JsonValue]
    strict: bool = True

    def __post_init__(self) -> None:
        _require_string(self.name, "name")
        _require_bool(self.strict, "strict")
        object.__setattr__(self, "schema", dict(_require_mapping(self.schema, "schema")))

    @classmethod
    def from_json(cls, value: object) -> "JsonSchemaOutput":
        payload = _require_mapping(value, "output")
        output_type = _require_string(_require_field(payload, "type"), "type")
        if output_type != "json_schema":
            raise ValueError("type must be json_schema")
        return cls(
            name=_require_string(_require_field(payload, "name"), "name"),
            schema=_require_mapping(_require_field(payload, "schema"), "schema"),
            strict=_require_bool(_require_field(payload, "strict"), "strict"),
        )

    def to_json(self) -> JsonObject:
        return {
            "type": "json_schema",
            "name": self.name,
            "schema": dict(self.schema),
            "strict": self.strict,
        }


@dataclass(frozen=True, slots=True)
class LlmRequest:
    request_id: str
    workflow: str
    model: str | None
    instructions: str
    input: Sequence[LlmMessage]
    output: JsonSchemaOutput
    required_capabilities: Sequence[LlmCapability | str] = field(default_factory=tuple)
    timeout_seconds: int = 300
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    llm_request_version: str = field(default=LLM_REQUEST_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        _require_string(self.workflow, "workflow")
        if self.model is not None:
            _require_string(self.model, "model")
        _require_string(self.instructions, "instructions")
        input_messages = tuple(self.input)
        if not input_messages:
            raise ValueError("input must not be empty")
        _require_positive_int(self.timeout_seconds, "timeout_seconds")
        object.__setattr__(self, "input", input_messages)
        object.__setattr__(self, "required_capabilities", _coerce_capabilities(self.required_capabilities))
        object.__setattr__(self, "metadata", dict(_require_mapping(self.metadata, "metadata")))

    @classmethod
    def from_json(cls, value: object) -> "LlmRequest":
        validate_json(value, SchemaName.LLM_REQUEST)
        payload = _require_mapping(value, "llm request")
        return cls(
            request_id=_require_string(_require_field(payload, "request_id"), "request_id"),
            workflow=_require_string(_require_field(payload, "workflow"), "workflow"),
            model=cast(str | None, _require_field(payload, "model")),
            instructions=_require_string(_require_field(payload, "instructions"), "instructions"),
            input=[
                LlmMessage.from_json(message)
                for message in _require_list(_require_field(payload, "input"), "input")
            ],
            output=JsonSchemaOutput.from_json(_require_field(payload, "output")),
            required_capabilities=[
                LlmCapability(_require_string(capability, "capability"))
                for capability in _require_list(
                    _require_field(payload, "required_capabilities"),
                    "required_capabilities",
                )
            ],
            timeout_seconds=_require_positive_int(_require_field(payload, "timeout_seconds"), "timeout_seconds"),
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        required_capabilities = cast(tuple[LlmCapability, ...], self.required_capabilities)
        return {
            "llm_request_version": self.llm_request_version,
            "request_id": self.request_id,
            "workflow": self.workflow,
            "model": self.model,
            "instructions": self.instructions,
            "input": [message.to_json() for message in self.input],
            "output": self.output.to_json(),
            "required_capabilities": [capability.value for capability in required_capabilities],
            "timeout_seconds": self.timeout_seconds,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class MeteredObject:
    name: str
    quantity: float | int
    unit: str

    def __post_init__(self) -> None:
        _require_string(self.name, "name")
        _require_non_negative_number(self.quantity, "quantity")
        _require_string(self.unit, "unit")

    @classmethod
    def from_json(cls, value: object) -> "MeteredObject":
        payload = _require_mapping(value, "metered object")
        return cls(
            name=_require_string(_require_field(payload, "name"), "name"),
            quantity=_require_non_negative_number(_require_field(payload, "quantity"), "quantity"),
            unit=_require_string(_require_field(payload, "unit"), "unit"),
        )

    def to_json(self) -> JsonObject:
        return {"name": self.name, "quantity": self.quantity, "unit": self.unit}


@dataclass(frozen=True, slots=True)
class LlmUsage:
    input_tokens: float | int | None
    cached_input_tokens: float | int | None
    output_tokens: float | int | None
    reasoning_tokens: float | int | None
    total_tokens: float | int | None
    metered_objects: Sequence[MeteredObject]
    started_at: str
    completed_at: str
    wall_seconds: float | int
    thinking_seconds: float | int | None

    def __post_init__(self) -> None:
        _require_optional_non_negative_number(self.input_tokens, "input_tokens")
        _require_optional_non_negative_number(self.cached_input_tokens, "cached_input_tokens")
        _require_optional_non_negative_number(self.output_tokens, "output_tokens")
        _require_optional_non_negative_number(self.reasoning_tokens, "reasoning_tokens")
        _require_optional_non_negative_number(self.total_tokens, "total_tokens")
        _require_string(self.started_at, "started_at")
        _require_string(self.completed_at, "completed_at")
        _require_non_negative_number(self.wall_seconds, "wall_seconds")
        _require_optional_non_negative_number(self.thinking_seconds, "thinking_seconds")
        object.__setattr__(self, "metered_objects", tuple(self.metered_objects))

    @classmethod
    def from_json(cls, value: object) -> "LlmUsage":
        payload = _require_mapping(value, "usage")
        return cls(
            input_tokens=_require_optional_non_negative_number(
                _require_field(payload, "input_tokens"),
                "input_tokens",
            ),
            cached_input_tokens=_require_optional_non_negative_number(
                _require_field(payload, "cached_input_tokens"),
                "cached_input_tokens",
            ),
            output_tokens=_require_optional_non_negative_number(
                _require_field(payload, "output_tokens"),
                "output_tokens",
            ),
            reasoning_tokens=_require_optional_non_negative_number(
                _require_field(payload, "reasoning_tokens"),
                "reasoning_tokens",
            ),
            total_tokens=_require_optional_non_negative_number(
                _require_field(payload, "total_tokens"),
                "total_tokens",
            ),
            metered_objects=[
                MeteredObject.from_json(metered)
                for metered in _require_list(_require_field(payload, "metered_objects"), "metered_objects")
            ],
            started_at=_require_string(_require_field(payload, "started_at"), "started_at"),
            completed_at=_require_string(_require_field(payload, "completed_at"), "completed_at"),
            wall_seconds=_require_non_negative_number(_require_field(payload, "wall_seconds"), "wall_seconds"),
            thinking_seconds=_require_optional_non_negative_number(
                _require_field(payload, "thinking_seconds"),
                "thinking_seconds",
            ),
        )

    def to_json(self) -> JsonObject:
        return {
            "input_tokens": self.input_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "total_tokens": self.total_tokens,
            "metered_objects": [metered.to_json() for metered in self.metered_objects],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "wall_seconds": self.wall_seconds,
            "thinking_seconds": self.thinking_seconds,
        }


@dataclass(frozen=True, slots=True)
class LlmOutput:
    value: JsonValue

    @classmethod
    def from_json(cls, value: object) -> "LlmOutput":
        payload = _require_mapping(value, "output")
        output_type = _require_string(_require_field(payload, "type"), "type")
        if output_type != "json":
            raise ValueError("type must be json")
        return cls(value=_require_field(payload, "value"))

    def to_json(self) -> JsonObject:
        return {"type": "json", "value": self.value}


@dataclass(frozen=True, slots=True)
class LlmResponse:
    request_id: str
    status: LlmStatus | str
    provider: ProviderName | str
    model: str | None
    output: LlmOutput | None
    usage: LlmUsage
    warnings: Sequence[str] = field(default_factory=tuple)
    llm_response_version: str = field(default=LLM_RESPONSE_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        object.__setattr__(self, "status", LlmStatus(self.status))
        object.__setattr__(self, "provider", ProviderName(self.provider))
        if self.model is not None:
            _require_string(self.model, "model")
        object.__setattr__(self, "warnings", _coerce_warnings(self.warnings))

    @classmethod
    def from_json(cls, value: object) -> "LlmResponse":
        validate_json(value, SchemaName.LLM_RESPONSE)
        payload = _require_mapping(value, "llm response")
        output = _require_field(payload, "output")
        return cls(
            request_id=_require_string(_require_field(payload, "request_id"), "request_id"),
            status=_require_string(_require_field(payload, "status"), "status"),
            provider=_require_string(_require_field(payload, "provider"), "provider"),
            model=cast(str | None, _require_field(payload, "model")),
            output=None if output is None else LlmOutput.from_json(output),
            usage=LlmUsage.from_json(_require_field(payload, "usage")),
            warnings=[
                _require_string(warning, "warning")
                for warning in _require_list(_require_field(payload, "warnings"), "warnings")
            ],
        )

    def to_json(self) -> JsonObject:
        status = cast(LlmStatus, self.status)
        provider = cast(ProviderName, self.provider)
        return {
            "llm_response_version": self.llm_response_version,
            "request_id": self.request_id,
            "status": status.value,
            "provider": provider.value,
            "model": self.model,
            "output": None if self.output is None else self.output.to_json(),
            "usage": self.usage.to_json(),
            "warnings": list(self.warnings),
        }


class LlmClient(Protocol):
    def complete(self, request: LlmRequest) -> LlmResponse: ...
