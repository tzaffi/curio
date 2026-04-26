from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import cast

from curio.llm_caller.models import (
    LlmAuthError,
    LlmCallerError,
    LlmCapability,
    LlmConfigurationError,
    LlmInvalidOutputError,
    LlmOutput,
    LlmProviderNotFoundError,
    LlmRejectedRequestError,
    LlmRequest,
    LlmResponse,
    LlmSchemaValidationError,
    LlmStatus,
    LlmTimeoutError,
    LlmUsage,
    MeteredObject,
    ProviderName,
    UnsupportedCapabilityError,
)


class ProviderErrorKind(StrEnum):
    CONFIGURATION = "configuration"
    MISSING_PROVIDER = "missing_provider"
    AUTH = "auth"
    TIMEOUT = "timeout"
    REJECTED_REQUEST = "rejected_request"
    INVALID_OUTPUT = "invalid_output"
    SCHEMA_VALIDATION = "schema_validation"


_PROVIDER_ERROR_TYPES: dict[ProviderErrorKind, type[LlmCallerError]] = {
    ProviderErrorKind.CONFIGURATION: LlmConfigurationError,
    ProviderErrorKind.MISSING_PROVIDER: LlmProviderNotFoundError,
    ProviderErrorKind.AUTH: LlmAuthError,
    ProviderErrorKind.TIMEOUT: LlmTimeoutError,
    ProviderErrorKind.REJECTED_REQUEST: LlmRejectedRequestError,
    ProviderErrorKind.INVALID_OUTPUT: LlmInvalidOutputError,
    ProviderErrorKind.SCHEMA_VALIDATION: LlmSchemaValidationError,
}


@dataclass(frozen=True, slots=True)
class ProviderClientConfig:
    provider: ProviderName | str
    capabilities: Sequence[LlmCapability | str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", ProviderName(self.provider))
        object.__setattr__(self, "capabilities", _coerce_declared_capabilities(self.capabilities))


@dataclass(frozen=True, slots=True)
class ProviderCallTiming:
    started_at: str
    completed_at: str
    wall_seconds: float


class ProviderClientBase:
    def __init__(self, config: ProviderClientConfig) -> None:
        self.config = config

    @property
    def provider(self) -> ProviderName:
        return cast(ProviderName, self.config.provider)

    @property
    def capabilities(self) -> tuple[LlmCapability, ...]:
        return cast(tuple[LlmCapability, ...], self.config.capabilities)

    def complete(self, request: LlmRequest) -> LlmResponse:
        require_provider_capabilities(request, self.capabilities)
        return self.complete_after_capability_check(request)

    def complete_after_capability_check(self, request: LlmRequest) -> LlmResponse:
        raise NotImplementedError("provider client must implement complete_after_capability_check")


def require_provider_capabilities(
    request: LlmRequest,
    available: Sequence[LlmCapability | str],
) -> None:
    available_capabilities = tuple(LlmCapability(capability) for capability in available)
    required_capabilities = cast(tuple[LlmCapability, ...], request.required_capabilities)
    missing = tuple(capability for capability in required_capabilities if capability not in available_capabilities)
    if missing:
        raise UnsupportedCapabilityError(required_capabilities, available_capabilities)


def measure_provider_call[CallResult](
    call: Callable[[], CallResult],
    *,
    clock: Callable[[], datetime] | None = None,
) -> tuple[CallResult, ProviderCallTiming]:
    get_now = _utc_now if clock is None else clock
    started_at = get_now()
    result = call()
    completed_at = get_now()
    timing = ProviderCallTiming(
        started_at=_format_utc(started_at),
        completed_at=_format_utc(completed_at),
        wall_seconds=(completed_at - started_at).total_seconds(),
    )
    return result, timing


def build_provider_usage(
    timing: ProviderCallTiming,
    *,
    input_tokens: float | int | None = None,
    cached_input_tokens: float | int | None = None,
    output_tokens: float | int | None = None,
    reasoning_tokens: float | int | None = None,
    total_tokens: float | int | None = None,
    metered_objects: Sequence[MeteredObject] = (),
    thinking_seconds: float | int | None = None,
) -> LlmUsage:
    return LlmUsage(
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        total_tokens=total_tokens,
        metered_objects=metered_objects,
        started_at=timing.started_at,
        completed_at=timing.completed_at,
        wall_seconds=timing.wall_seconds,
        thinking_seconds=thinking_seconds,
    )


def build_json_llm_response(
    request: LlmRequest,
    *,
    provider: ProviderName | str,
    model: str | None,
    output_value: object,
    usage: LlmUsage,
    warnings: Sequence[str] = (),
) -> LlmResponse:
    return LlmResponse(
        request_id=request.request_id,
        status=LlmStatus.SUCCEEDED,
        provider=provider,
        model=model,
        output=LlmOutput(value=output_value),
        usage=usage,
        warnings=warnings,
    )


def map_provider_error(kind: ProviderErrorKind | str, detail: str) -> LlmCallerError:
    return _PROVIDER_ERROR_TYPES[ProviderErrorKind(kind)](detail)


def _coerce_declared_capabilities(values: Sequence[LlmCapability | str]) -> tuple[LlmCapability, ...]:
    capabilities = tuple(LlmCapability(value) for value in values)
    if not capabilities:
        raise ValueError("capabilities must not be empty")
    if len(capabilities) != len(set(capabilities)):
        raise ValueError("capabilities must be unique")
    return capabilities


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
