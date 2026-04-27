from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, cast

from curio.schemas import SchemaName, validate_json

JsonObject = dict[str, Any]
JsonValue = Any

LLM_REQUEST_VERSION = "curio-llm-request.v1"
LLM_RESPONSE_VERSION = "curio-llm-response.v1"


class ProviderName(StrEnum):
    CODEX_CLI = "codex_cli"
    OPENAI_API = "openai_api"
    GOOGLE_DOCUMENT_AI = "google_document_ai"


class LlmCapability(StrEnum):
    TEXT_GENERATION = "text_generation"
    JSON_SCHEMA_OUTPUT = "json_schema_output"
    TOKEN_USAGE = "token_usage"
    CACHED_INPUT_USAGE = "cached_input_usage"
    REASONING_TOKEN_USAGE = "reasoning_token_usage"
    THINKING_TIME = "thinking_time"
    SUBPROCESS = "subprocess"
    FILE_INPUT = "file_input"
    IMAGE_INPUT = "image_input"
    PDF_INPUT = "pdf_input"
    DOCUMENT_TEXT_EXTRACTION = "document_text_extraction"
    OCR = "ocr"
    LAYOUT_EXTRACTION = "layout_extraction"
    MARKDOWN_OUTPUT = "markdown_output"
    PLAIN_TEXT_OUTPUT = "plain_text_output"
    SUGGESTED_FILE_OUTPUT = "suggested_file_output"
    MULTIPLE_FILE_OUTPUT = "multiple_file_output"
    RELATIVE_PATH_OUTPUT = "relative_path_output"
    METERED_PAGE_USAGE = "metered_page_usage"


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
class LocalFileContentPart:
    path: str
    mime_type: str
    sha256: str
    name: str | None = None

    def __post_init__(self) -> None:
        _require_string(self.path, "path")
        if not Path(self.path).is_absolute():
            raise ValueError("path must be absolute")
        _require_string(self.mime_type, "mime_type")
        _require_string(self.sha256, "sha256")
        if self.name is not None:
            _require_string(self.name, "name")

    @classmethod
    def from_json(cls, value: object) -> "LocalFileContentPart":
        payload = _require_mapping(value, "content part")
        part_type = _require_string(_require_field(payload, "type"), "type")
        if part_type != "local_file":
            raise ValueError("type must be local_file")
        name = payload.get("name")
        return cls(
            path=_require_string(_require_field(payload, "path"), "path"),
            mime_type=_require_string(_require_field(payload, "mime_type"), "mime_type"),
            sha256=_require_string(_require_field(payload, "sha256"), "sha256"),
            name=None if name is None else _require_string(name, "name"),
        )

    def to_json(self) -> JsonObject:
        return {
            "type": "local_file",
            "path": self.path,
            "mime_type": self.mime_type,
            "sha256": self.sha256,
            "name": self.name,
        }


LlmContentPart = TextContentPart | LocalFileContentPart


def content_part_from_json(value: object) -> LlmContentPart:
    payload = _require_mapping(value, "content part")
    part_type = _require_string(_require_field(payload, "type"), "type")
    if part_type == "text":
        return TextContentPart.from_json(payload)
    if part_type == "local_file":
        return LocalFileContentPart.from_json(payload)
    raise ValueError("type must be text or local_file")


@dataclass(frozen=True, slots=True)
class LlmMessage:
    role: LlmMessageRole | str
    content: Sequence[LlmContentPart]

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
                content_part_from_json(part)
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
    instructions: str
    input: Sequence[LlmMessage]
    output: JsonSchemaOutput
    required_capabilities: Sequence[LlmCapability | str] = field(default_factory=tuple)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    llm_request_version: str = field(default=LLM_REQUEST_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        _require_string(self.workflow, "workflow")
        _require_string(self.instructions, "instructions")
        input_messages = tuple(self.input)
        if not input_messages:
            raise ValueError("input must not be empty")
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
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        required_capabilities = cast(tuple[LlmCapability, ...], self.required_capabilities)
        return {
            "llm_request_version": self.llm_request_version,
            "request_id": self.request_id,
            "workflow": self.workflow,
            "instructions": self.instructions,
            "input": [message.to_json() for message in self.input],
            "output": self.output.to_json(),
            "required_capabilities": [capability.value for capability in required_capabilities],
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
class LlmPricing:
    currency: str
    basis: str
    input_price_per_million: float | int
    cached_input_price_per_million: float | int
    output_price_per_million: float | int
    metered_price_per_thousand: float | int | None = None
    metered_name: str | None = None
    metered_unit: str | None = None

    def __post_init__(self) -> None:
        if self.currency != "USD":
            raise ValueError("currency must be USD")
        if self.basis != "api_equivalent":
            raise ValueError("basis must be api_equivalent")
        _require_non_negative_number(self.input_price_per_million, "input_price_per_million")
        _require_non_negative_number(self.cached_input_price_per_million, "cached_input_price_per_million")
        _require_non_negative_number(self.output_price_per_million, "output_price_per_million")
        if self.metered_price_per_thousand is not None:
            _require_non_negative_number(self.metered_price_per_thousand, "metered_price_per_thousand")
            _require_string(self.metered_name, "metered_name")
            _require_string(self.metered_unit, "metered_unit")
        elif self.metered_name is not None or self.metered_unit is not None:
            raise ValueError("metered pricing fields must be configured together")

    @classmethod
    def from_json(cls, value: object) -> "LlmPricing":
        payload = _require_mapping(value, "pricing")
        return cls(
            currency=_require_string(_require_field(payload, "currency"), "currency"),
            basis=_require_string(_require_field(payload, "basis"), "basis"),
            input_price_per_million=_require_non_negative_number(
                _require_field(payload, "input_price_per_million"),
                "input_price_per_million",
            ),
            cached_input_price_per_million=_require_non_negative_number(
                _require_field(payload, "cached_input_price_per_million"),
                "cached_input_price_per_million",
            ),
            output_price_per_million=_require_non_negative_number(
                _require_field(payload, "output_price_per_million"),
                "output_price_per_million",
            ),
            metered_price_per_thousand=_require_optional_non_negative_number(
                payload.get("metered_price_per_thousand"),
                "metered_price_per_thousand",
            ),
            metered_name=None
            if payload.get("metered_name") is None
            else _require_string(payload.get("metered_name"), "metered_name"),
            metered_unit=None
            if payload.get("metered_unit") is None
            else _require_string(payload.get("metered_unit"), "metered_unit"),
        )

    def to_json(self) -> JsonObject:
        payload: JsonObject = {
            "currency": self.currency,
            "basis": self.basis,
            "input_price_per_million": self.input_price_per_million,
            "cached_input_price_per_million": self.cached_input_price_per_million,
            "output_price_per_million": self.output_price_per_million,
        }
        if self.metered_price_per_thousand is not None:
            payload["metered_price_per_thousand"] = self.metered_price_per_thousand
            payload["metered_name"] = self.metered_name
            payload["metered_unit"] = self.metered_unit
        return payload


@dataclass(frozen=True, slots=True)
class LlmCostEstimate:
    currency: str
    basis: str
    amount: float | int
    input_price_per_million: float | int
    cached_input_price_per_million: float | int
    output_price_per_million: float | int
    metered_price_per_thousand: float | int | None = None
    metered_name: str | None = None
    metered_unit: str | None = None

    def __post_init__(self) -> None:
        if self.currency != "USD":
            raise ValueError("currency must be USD")
        if self.basis != "api_equivalent":
            raise ValueError("basis must be api_equivalent")
        _require_non_negative_number(self.amount, "amount")
        _require_non_negative_number(self.input_price_per_million, "input_price_per_million")
        _require_non_negative_number(self.cached_input_price_per_million, "cached_input_price_per_million")
        _require_non_negative_number(self.output_price_per_million, "output_price_per_million")
        if self.metered_price_per_thousand is not None:
            _require_non_negative_number(self.metered_price_per_thousand, "metered_price_per_thousand")
            _require_string(self.metered_name, "metered_name")
            _require_string(self.metered_unit, "metered_unit")
        elif self.metered_name is not None or self.metered_unit is not None:
            raise ValueError("metered pricing fields must be configured together")

    @classmethod
    def from_json(cls, value: object) -> "LlmCostEstimate":
        payload = _require_mapping(value, "cost_estimate")
        return cls(
            currency=_require_string(_require_field(payload, "currency"), "currency"),
            basis=_require_string(_require_field(payload, "basis"), "basis"),
            amount=_require_non_negative_number(_require_field(payload, "amount"), "amount"),
            input_price_per_million=_require_non_negative_number(
                _require_field(payload, "input_price_per_million"),
                "input_price_per_million",
            ),
            cached_input_price_per_million=_require_non_negative_number(
                _require_field(payload, "cached_input_price_per_million"),
                "cached_input_price_per_million",
            ),
            output_price_per_million=_require_non_negative_number(
                _require_field(payload, "output_price_per_million"),
                "output_price_per_million",
            ),
            metered_price_per_thousand=_require_optional_non_negative_number(
                payload.get("metered_price_per_thousand"),
                "metered_price_per_thousand",
            ),
            metered_name=None
            if payload.get("metered_name") is None
            else _require_string(payload.get("metered_name"), "metered_name"),
            metered_unit=None
            if payload.get("metered_unit") is None
            else _require_string(payload.get("metered_unit"), "metered_unit"),
        )

    def to_json(self) -> JsonObject:
        payload: JsonObject = {
            "currency": self.currency,
            "basis": self.basis,
            "amount": self.amount,
            "input_price_per_million": self.input_price_per_million,
            "cached_input_price_per_million": self.cached_input_price_per_million,
            "output_price_per_million": self.output_price_per_million,
        }
        if self.metered_price_per_thousand is not None:
            payload["metered_price_per_thousand"] = self.metered_price_per_thousand
            payload["metered_name"] = self.metered_name
            payload["metered_unit"] = self.metered_unit
        return payload


def estimate_llm_cost(usage: LlmUsage, pricing: LlmPricing | None) -> LlmCostEstimate | None:
    if pricing is None:
        return None
    token_amount = _estimate_token_cost(usage, pricing)
    metered_amount = _estimate_metered_cost(usage, pricing)
    if token_amount is None and metered_amount is None:
        return None
    amount = (0 if token_amount is None else token_amount) + (0 if metered_amount is None else metered_amount)
    return LlmCostEstimate(
        currency=pricing.currency,
        basis=pricing.basis,
        amount=amount,
        input_price_per_million=pricing.input_price_per_million,
        cached_input_price_per_million=pricing.cached_input_price_per_million,
        output_price_per_million=pricing.output_price_per_million,
        metered_price_per_thousand=pricing.metered_price_per_thousand,
        metered_name=pricing.metered_name,
        metered_unit=pricing.metered_unit,
    )


def _estimate_token_cost(usage: LlmUsage, pricing: LlmPricing) -> float | int | None:
    if usage.input_tokens is None or usage.output_tokens is None:
        return None
    cached_input_tokens = 0 if usage.cached_input_tokens is None else usage.cached_input_tokens
    return (
        usage.input_tokens * pricing.input_price_per_million
        + cached_input_tokens * pricing.cached_input_price_per_million
        + usage.output_tokens * pricing.output_price_per_million
    ) / 1_000_000


def _estimate_metered_cost(usage: LlmUsage, pricing: LlmPricing) -> float | int | None:
    if pricing.metered_price_per_thousand is None:
        return None
    for metered_object in usage.metered_objects:
        if metered_object.name == pricing.metered_name and metered_object.unit == pricing.metered_unit:
            return metered_object.quantity * pricing.metered_price_per_thousand / 1_000
    return None


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
