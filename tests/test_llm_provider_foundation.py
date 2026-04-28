from datetime import UTC, datetime, timedelta

import pytest

from curio.llm_caller import (
    JsonSchemaOutput,
    LlmAuthError,
    LlmCapability,
    LlmConfigurationError,
    LlmInvalidOutputError,
    LlmMessage,
    LlmProviderNotFoundError,
    LlmRejectedRequestError,
    LlmRequest,
    LlmResponse,
    LlmSchemaValidationError,
    LlmStatus,
    LlmTimeoutError,
    LlmUsage,
    MeteredObject,
    ProviderCallTiming,
    ProviderClientBase,
    ProviderClientConfig,
    ProviderErrorKind,
    ProviderName,
    TextContentPart,
    UnsupportedCapabilityError,
    build_json_llm_response,
    build_provider_usage,
    map_provider_error,
    measure_provider_call,
)


def make_request() -> LlmRequest:
    return LlmRequest(
        request_id="translate-test",
        workflow="translate",
        instructions="Return JSON.",
        input=[LlmMessage(role="user", content=[TextContentPart(text="Translate this.")])],
        output=JsonSchemaOutput(name="curio_translation_model_output", schema={"type": "object"}),
        required_capabilities=[
            LlmCapability.TEXT_GENERATION,
            LlmCapability.JSON_SCHEMA_OUTPUT,
        ],
        metadata={},
    )


def make_timing() -> ProviderCallTiming:
    return ProviderCallTiming(
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:03Z",
        wall_seconds=3,
    )


def make_usage() -> LlmUsage:
    return build_provider_usage(make_timing(), input_tokens=10, output_tokens=4, total_tokens=14)


def test_provider_client_config_normalizes_values_and_rejects_invalid_shapes() -> None:
    config = ProviderClientConfig(
        provider="codex_cli",
        capabilities=["text_generation", LlmCapability.JSON_SCHEMA_OUTPUT],
    )

    assert config.provider == ProviderName.CODEX_CLI
    assert config.capabilities == (
        LlmCapability.TEXT_GENERATION,
        LlmCapability.JSON_SCHEMA_OUTPUT,
    )
    with pytest.raises(ValueError, match="capabilities must not be empty"):
        ProviderClientConfig(provider="codex_cli", capabilities=[])

    with pytest.raises(ValueError, match="capabilities must be unique"):
        ProviderClientConfig(provider="codex_cli", capabilities=["text_generation", "text_generation"])


def test_provider_base_checks_capabilities_before_provider_work() -> None:
    request = make_request()

    class FakeClient(ProviderClientBase):
        def __init__(self, config: ProviderClientConfig) -> None:
            super().__init__(config)
            self.provider_work_count = 0

        def complete_after_capability_check(self, request: LlmRequest) -> LlmResponse:
            self.provider_work_count += 1
            return build_json_llm_response(
                request,
                provider=self.provider,
                model="provider-model",
                output_value={"ok": True},
                usage=make_usage(),
            )

    unsupported = FakeClient(
        ProviderClientConfig(
            provider="codex_cli",
            capabilities=[LlmCapability.TEXT_GENERATION],
        )
    )

    with pytest.raises(UnsupportedCapabilityError, match="json_schema_output"):
        unsupported.complete(request)

    assert unsupported.provider_work_count == 0

    supported = FakeClient(
        ProviderClientConfig(
            provider=ProviderName.CODEX_CLI,
            capabilities=[LlmCapability.TEXT_GENERATION, LlmCapability.JSON_SCHEMA_OUTPUT],
        )
    )

    response = supported.complete(request)

    assert supported.provider_work_count == 1
    assert supported.provider == ProviderName.CODEX_CLI
    assert supported.capabilities == (
        LlmCapability.TEXT_GENERATION,
        LlmCapability.JSON_SCHEMA_OUTPUT,
    )
    assert response.provider == ProviderName.CODEX_CLI
    assert response.model == "provider-model"
    assert response.output is not None
    assert response.output.value == {"ok": True}


def test_provider_base_requires_provider_specific_implementation() -> None:
    client = ProviderClientBase(
        ProviderClientConfig(
            provider="codex_cli",
            capabilities=[LlmCapability.TEXT_GENERATION, LlmCapability.JSON_SCHEMA_OUTPUT],
        )
    )

    with pytest.raises(NotImplementedError, match="provider client must implement"):
        client.complete(make_request())


def test_measure_provider_call_and_build_provider_usage() -> None:
    started_at = datetime(2026, 4, 24, 15, 20, 0, tzinfo=UTC)
    completed_at = started_at + timedelta(seconds=2.5)
    moments = iter([started_at, completed_at])

    result, timing = measure_provider_call(lambda: "provider result", clock=lambda: next(moments))

    assert result == "provider result"
    assert timing == ProviderCallTiming(
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:02.500000Z",
        wall_seconds=2.5,
    )

    usage = build_provider_usage(
        timing,
        input_tokens=10,
        cached_input_tokens=3,
        output_tokens=4,
        reasoning_tokens=2,
        total_tokens=14,
        metered_objects=[MeteredObject(name="request", quantity=1, unit="count")],
        thinking_seconds=0.5,
    )

    assert usage.started_at == timing.started_at
    assert usage.completed_at == timing.completed_at
    assert usage.wall_seconds == 2.5
    assert usage.cached_input_tokens == 3
    assert usage.metered_objects == (MeteredObject(name="request", quantity=1, unit="count"),)
    assert usage.thinking_seconds == 0.5

    real_result, real_timing = measure_provider_call(lambda: "ok")
    assert real_result == "ok"
    assert real_timing.started_at.endswith("Z")
    assert real_timing.completed_at.endswith("Z")
    assert real_timing.wall_seconds >= 0


def test_build_json_llm_response_uses_provider_model() -> None:
    response = build_json_llm_response(
        make_request(),
        provider="openai_api",
        model="provider-model",
        output_value={"translated_blocks": []},
        usage=make_usage(),
        warnings=["provider warning"],
    )

    assert response.status == LlmStatus.SUCCEEDED
    assert response.provider == ProviderName.OPENAI_API
    assert response.model == "provider-model"
    assert response.output is not None
    assert response.output.value == {"translated_blocks": []}
    assert response.warnings == ("provider warning",)


def test_build_json_llm_response_deduplicates_provider_warnings() -> None:
    response = build_json_llm_response(
        make_request(),
        provider="codex_cli",
        model="provider-model",
        output_value={"translated_blocks": []},
        usage=make_usage(),
        warnings=["transient warning", "transient warning", "other warning", "transient warning"],
    )

    assert response.warnings == ("transient warning", "other warning")


def test_map_provider_error_returns_typed_errors() -> None:
    cases: list[tuple[ProviderErrorKind | str, type[Exception]]] = [
        (ProviderErrorKind.CONFIGURATION, LlmConfigurationError),
        (ProviderErrorKind.MISSING_PROVIDER, LlmProviderNotFoundError),
        (ProviderErrorKind.AUTH, LlmAuthError),
        (ProviderErrorKind.TIMEOUT, LlmTimeoutError),
        (ProviderErrorKind.REJECTED_REQUEST, LlmRejectedRequestError),
        (ProviderErrorKind.INVALID_OUTPUT, LlmInvalidOutputError),
        ("schema_validation", LlmSchemaValidationError),
    ]

    for kind, error_type in cases:
        error = map_provider_error(kind, "provider failed")
        assert isinstance(error, error_type)
        assert str(error) == "provider failed"
