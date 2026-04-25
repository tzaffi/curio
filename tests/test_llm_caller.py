from typing import cast

import pytest

from curio.llm_caller import (
    JsonSchemaOutput,
    LlmCapability,
    LlmClient,
    LlmMessage,
    LlmMessageRole,
    LlmOutput,
    LlmRequest,
    LlmResponse,
    LlmStatus,
    LlmUsage,
    MeteredObject,
    ProviderName,
    TextContentPart,
    UnsupportedCapabilityError,
)
from curio.schemas import SchemaName, validate_json


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=10,
        cached_input_tokens=None,
        output_tokens=4,
        reasoning_tokens=None,
        total_tokens=14,
        metered_objects=[MeteredObject(name="image", quantity=1, unit="count")],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:03Z",
        wall_seconds=3,
        thinking_seconds=None,
    )


def make_request() -> LlmRequest:
    return LlmRequest(
        request_id="translate-test",
        workflow="translate",
        model="gpt-test",
        instructions="Return JSON.",
        input=[
            LlmMessage(
                role="user",
                content=[TextContentPart(text="Translate this.")],
            )
        ],
        output=JsonSchemaOutput(name="curio_translation_model_output", schema={"type": "object"}),
        required_capabilities=[
            "text_generation",
            LlmCapability.JSON_SCHEMA_OUTPUT,
        ],
        timeout_seconds=300,
        metadata={"source": "test"},
    )


def make_response() -> LlmResponse:
    return LlmResponse(
        request_id="translate-test",
        status="succeeded",
        provider="codex_cli",
        model="gpt-test",
        output=LlmOutput(value={"ok": True}),
        usage=make_usage(),
        warnings=["provider warning"],
    )


def test_llm_request_serializes_to_schema_payload() -> None:
    request = make_request()

    payload = request.to_json()

    assert request.input[0].role == LlmMessageRole.USER
    assert request.required_capabilities == (
        LlmCapability.TEXT_GENERATION,
        LlmCapability.JSON_SCHEMA_OUTPUT,
    )
    assert payload["llm_request_version"] == "curio-llm-request.v1"
    assert payload["input"][0]["content"][0] == {"type": "text", "text": "Translate this."}
    validate_json(payload, SchemaName.LLM_REQUEST)


def test_llm_request_preserves_accepted_string_values() -> None:
    request = LlmRequest(
        request_id=" translate-test ",
        workflow="translate",
        model=None,
        instructions="Return JSON.",
        input=[LlmMessage(role="user", content=[TextContentPart(text=" keep spacing ")])],
        output=JsonSchemaOutput(name="output", schema={}),
    )

    payload = request.to_json()

    assert payload["request_id"] == " translate-test "
    assert payload["input"][0]["content"][0]["text"] == " keep spacing "


def test_llm_response_serializes_to_schema_payload() -> None:
    response = make_response()

    payload = response.to_json()

    assert response.status == LlmStatus.SUCCEEDED
    assert response.provider == ProviderName.CODEX_CLI
    assert payload["usage"]["metered_objects"] == [{"name": "image", "quantity": 1, "unit": "count"}]
    validate_json(payload, SchemaName.LLM_RESPONSE)


def test_llm_response_allows_null_output_for_non_success_status() -> None:
    response = LlmResponse(
        request_id="translate-test",
        status=LlmStatus.FAILED,
        provider=ProviderName.OPENAI_API,
        model=None,
        output=None,
        usage=make_usage(),
    )

    validate_json(response.to_json(), SchemaName.LLM_RESPONSE)


def test_llm_client_protocol_accepts_fake_client() -> None:
    request = make_request()
    response = make_response()

    class FakeClient:
        def complete(self, request: LlmRequest) -> LlmResponse:
            assert request.workflow == "translate"
            return response

    client: LlmClient = FakeClient()

    assert client.complete(request) is response


def test_unsupported_capability_error_reports_missing_capabilities() -> None:
    error = UnsupportedCapabilityError(
        required=[LlmCapability.TEXT_GENERATION, "json_schema_output"],
        available=["text_generation"],
    )

    assert error.missing == (LlmCapability.JSON_SCHEMA_OUTPUT,)
    assert "json_schema_output" in str(error)


def test_unsupported_capability_error_handles_no_missing_capabilities() -> None:
    error = UnsupportedCapabilityError(
        required=["text_generation"],
        available=[LlmCapability.TEXT_GENERATION],
    )

    assert error.missing == ()
    assert str(error).endswith("none")


def test_llm_message_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="content must not be empty"):
        LlmMessage(role="user", content=[])


def test_llm_request_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="input must not be empty"):
        LlmRequest(
            request_id="translate-test",
            workflow="translate",
            model=None,
            instructions="Return JSON.",
            input=[],
            output=JsonSchemaOutput(name="output", schema={}),
        )


def test_llm_request_rejects_invalid_scalar_fields() -> None:
    with pytest.raises(ValueError, match="request_id must not be empty"):
        LlmRequest(
            request_id=" ",
            workflow="translate",
            model=None,
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
        )

    with pytest.raises(ValueError, match="request_id must be a string"):
        LlmRequest(
            request_id=cast(str, None),
            workflow="translate",
            model=None,
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
        )

    with pytest.raises(ValueError, match="timeout_seconds must be a positive integer"):
        LlmRequest(
            request_id="translate-test",
            workflow="translate",
            model=None,
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
            timeout_seconds=0,
        )

    with pytest.raises(ValueError, match="timeout_seconds must be a positive integer"):
        LlmRequest(
            request_id="translate-test",
            workflow="translate",
            model=None,
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
            timeout_seconds=False,
        )


def test_llm_request_rejects_duplicate_capabilities() -> None:
    with pytest.raises(ValueError, match="capabilities must be unique"):
        LlmRequest(
            request_id="translate-test",
            workflow="translate",
            model=None,
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
            required_capabilities=["text_generation", "text_generation"],
        )


def test_json_schema_output_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        JsonSchemaOutput(name=" ", schema={})

    with pytest.raises(ValueError, match="schema must be an object"):
        JsonSchemaOutput(name="output", schema=cast(dict[str, object], []))


def test_text_content_part_rejects_invalid_text() -> None:
    with pytest.raises(ValueError, match="text must not be empty"):
        TextContentPart(text=" ")

    with pytest.raises(ValueError, match="text must be a string"):
        TextContentPart(text=cast(str, None))


def test_metered_object_and_usage_reject_negative_numbers() -> None:
    with pytest.raises(ValueError, match="quantity must be a non-negative number"):
        MeteredObject(name="image", quantity=-1, unit="count")

    with pytest.raises(ValueError, match="quantity must be a non-negative number"):
        MeteredObject(name="image", quantity=True, unit="count")

    with pytest.raises(ValueError, match="input_tokens must be a non-negative number"):
        LlmUsage(
            input_tokens=-1,
            cached_input_tokens=None,
            output_tokens=None,
            reasoning_tokens=None,
            total_tokens=None,
            metered_objects=[],
            started_at="2026-04-24T15:20:00Z",
            completed_at="2026-04-24T15:20:03Z",
            wall_seconds=3,
            thinking_seconds=None,
        )

    with pytest.raises(ValueError, match="input_tokens must be a non-negative number"):
        LlmUsage(
            input_tokens=True,
            cached_input_tokens=None,
            output_tokens=None,
            reasoning_tokens=None,
            total_tokens=None,
            metered_objects=[],
            started_at="2026-04-24T15:20:00Z",
            completed_at="2026-04-24T15:20:03Z",
            wall_seconds=3,
            thinking_seconds=None,
        )


def test_llm_response_rejects_duplicate_warnings() -> None:
    with pytest.raises(ValueError, match="warnings must be unique"):
        LlmResponse(
            request_id="translate-test",
            status="succeeded",
            provider="codex_cli",
            model=None,
            output=LlmOutput(value={}),
            usage=make_usage(),
            warnings=["same", "same"],
        )
