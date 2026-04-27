from typing import cast

import pytest

from curio.llm_caller import (
    JsonSchemaOutput,
    LlmCapability,
    LlmClient,
    LlmCostEstimate,
    LlmMessage,
    LlmMessageRole,
    LlmOutput,
    LlmPricing,
    LlmRequest,
    LlmResponse,
    LlmStatus,
    LlmUsage,
    LocalFileContentPart,
    MeteredObject,
    ProviderName,
    TextContentPart,
    UnsupportedCapabilityError,
    content_part_from_json,
    estimate_llm_cost,
)
from curio.schemas import SchemaName, SchemaValidationError, validate_json


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


def make_pricing() -> LlmPricing:
    return LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=5.0,
        cached_input_price_per_million=0.5,
        output_price_per_million=30.0,
    )


def make_cost_estimate() -> LlmCostEstimate:
    return LlmCostEstimate(
        currency="USD",
        basis="api_equivalent",
        amount=0.00017,
        input_price_per_million=5.0,
        cached_input_price_per_million=0.5,
        output_price_per_million=30.0,
    )


def make_request() -> LlmRequest:
    return LlmRequest(
        request_id="translate-test",
        workflow="translate",
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


def test_llm_request_serializes_local_file_content_part(tmp_path) -> None:
    path = tmp_path / "scan.png"
    path.write_bytes(b"png")
    request = LlmRequest(
        request_id="textify-test",
        workflow="textify",
        instructions="Extract.",
        input=[
            LlmMessage(
                role="user",
                content=[
                    TextContentPart(text="see file"),
                    LocalFileContentPart(
                        path=str(path),
                        mime_type="image/png",
                        sha256="abc123",
                        name="scan.png",
                    ),
                ],
            )
        ],
        output=JsonSchemaOutput(name="output", schema={}),
        required_capabilities=["file_input"],
        metadata={},
    )

    payload = request.to_json()

    assert payload["input"][0]["content"][1]["type"] == "local_file"
    assert LlmRequest.from_json(payload) == request
    validate_json(payload, SchemaName.LLM_REQUEST)


def test_llm_request_parses_from_schema_payload() -> None:
    payload = make_request().to_json()

    request = LlmRequest.from_json(payload)

    assert request == make_request()


def test_llm_request_from_json_rejects_schema_invalid_payload() -> None:
    payload = make_request().to_json()
    payload["required_capabilities"] = ["chatgpt_auth"]

    with pytest.raises(SchemaValidationError, match="chatgpt_auth"):
        LlmRequest.from_json(payload)


def test_llm_request_preserves_accepted_string_values() -> None:
    request = LlmRequest(
        request_id=" translate-test ",
        workflow="translate",
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


def test_llm_response_parses_from_schema_payload() -> None:
    payload = make_response().to_json()

    response = LlmResponse.from_json(payload)

    assert response == make_response()


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


def test_llm_response_from_json_allows_null_output() -> None:
    response = LlmResponse(
        request_id="translate-test",
        status=LlmStatus.FAILED,
        provider=ProviderName.OPENAI_API,
        model=None,
        output=None,
        usage=make_usage(),
    )

    assert LlmResponse.from_json(response.to_json()) == response


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


def test_estimate_llm_cost_uses_api_equivalent_pricing() -> None:
    estimate = estimate_llm_cost(make_usage(), make_pricing())

    assert estimate == make_cost_estimate()
    assert estimate_llm_cost(make_usage(), None) is None
    assert estimate_llm_cost(
        LlmUsage(
            input_tokens=None,
            cached_input_tokens=None,
            output_tokens=4,
            reasoning_tokens=None,
            total_tokens=4,
            metered_objects=[],
            started_at="2026-04-24T15:20:00Z",
            completed_at="2026-04-24T15:20:03Z",
            wall_seconds=3,
            thinking_seconds=None,
        ),
        make_pricing(),
    ) is None
    assert estimate_llm_cost(
        LlmUsage(
            input_tokens=10,
            cached_input_tokens=None,
            output_tokens=4,
            reasoning_tokens=None,
            total_tokens=14,
            metered_objects=[],
            started_at="2026-04-24T15:20:00Z",
            completed_at="2026-04-24T15:20:03Z",
            wall_seconds=3,
            thinking_seconds=None,
        ),
        make_pricing(),
    ) == LlmCostEstimate(
        currency="USD",
        basis="api_equivalent",
        amount=0.00017,
        input_price_per_million=5.0,
        cached_input_price_per_million=0.5,
        output_price_per_million=30.0,
    )


def test_estimate_llm_cost_supports_metered_page_pricing() -> None:
    pricing = LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0,
        cached_input_price_per_million=0,
        output_price_per_million=0,
        metered_price_per_thousand=10,
        metered_name="document_ai_pages",
        metered_unit="page",
    )
    usage = LlmUsage(
        input_tokens=None,
        cached_input_tokens=None,
        output_tokens=None,
        reasoning_tokens=None,
        total_tokens=None,
        metered_objects=[MeteredObject(name="document_ai_pages", quantity=3, unit="page")],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:03Z",
        wall_seconds=3,
        thinking_seconds=None,
    )

    estimate = estimate_llm_cost(usage, pricing)

    assert estimate == LlmCostEstimate(
        "USD",
        "api_equivalent",
        0.03,
        0,
        0,
        0,
        10,
        "document_ai_pages",
        "page",
    )
    assert LlmPricing.from_json(pricing.to_json()) == pricing
    assert LlmCostEstimate.from_json(estimate.to_json()) == estimate
    assert estimate_llm_cost(
        LlmUsage(None, None, None, None, None, [], "2026-04-24T15:20:00Z", "2026-04-24T15:20:03Z", 3, None),
        pricing,
    ) is None
    with pytest.raises(ValueError, match="metered pricing fields"):
        LlmPricing("USD", "api_equivalent", 0, 0, 0, metered_name="document_ai_pages")

    with pytest.raises(ValueError, match="metered pricing fields"):
        LlmCostEstimate("USD", "api_equivalent", 0, 0, 0, 0, metered_name="document_ai_pages")


def test_llm_message_rejects_empty_content() -> None:
    with pytest.raises(ValueError, match="content must not be empty"):
        LlmMessage(role="user", content=[])


def test_llm_nested_models_parse_from_json() -> None:
    assert TextContentPart.from_json({"type": "text", "text": "hello"}) == TextContentPart(text="hello")
    assert LocalFileContentPart.from_json(
        {
            "type": "local_file",
            "path": "/tmp/scan.png",
            "mime_type": "image/png",
            "sha256": "abc",
            "name": None,
        }
    ) == LocalFileContentPart(path="/tmp/scan.png", mime_type="image/png", sha256="abc")
    assert content_part_from_json({"type": "text", "text": "hello"}) == TextContentPart(text="hello")
    assert LlmMessage.from_json(
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "hello"}],
        }
    ) == LlmMessage(role=LlmMessageRole.ASSISTANT, content=[TextContentPart(text="hello")])
    assert JsonSchemaOutput.from_json(
        {
            "type": "json_schema",
            "name": "output",
            "schema": {"type": "object"},
            "strict": True,
        }
    ) == JsonSchemaOutput(name="output", schema={"type": "object"}, strict=True)
    assert MeteredObject.from_json({"name": "image", "quantity": 1, "unit": "count"}) == MeteredObject(
        name="image",
        quantity=1,
        unit="count",
    )
    assert LlmUsage.from_json(make_usage().to_json()) == make_usage()
    assert LlmPricing.from_json(make_pricing().to_json()) == make_pricing()
    assert LlmCostEstimate.from_json(make_cost_estimate().to_json()) == make_cost_estimate()
    assert LlmOutput.from_json({"type": "json", "value": {"ok": True}}) == LlmOutput(value={"ok": True})


def test_llm_nested_parsers_reject_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="type must be text"):
        TextContentPart.from_json({"type": "image", "text": "hello"})

    with pytest.raises(ValueError, match="text is required"):
        TextContentPart.from_json({"type": "text"})

    with pytest.raises(ValueError, match="path must be absolute"):
        LocalFileContentPart(path="relative.png", mime_type="image/png", sha256="abc")

    with pytest.raises(ValueError, match="type must be local_file"):
        LocalFileContentPart.from_json({"type": "text", "path": "/tmp/x", "mime_type": "image/png", "sha256": "abc"})

    with pytest.raises(ValueError, match="type must be text or local_file"):
        content_part_from_json({"type": "audio", "path": "/tmp/x"})

    with pytest.raises(ValueError, match="content must be a list"):
        LlmMessage.from_json({"role": "user", "content": {}})

    with pytest.raises(ValueError, match="strict must be a boolean"):
        JsonSchemaOutput.from_json(
            {
                "type": "json_schema",
                "name": "output",
                "schema": {},
                "strict": "true",
            }
        )

    with pytest.raises(ValueError, match="type must be json_schema"):
        JsonSchemaOutput.from_json({"type": "json", "name": "output", "schema": {}, "strict": True})

    with pytest.raises(ValueError, match="type must be json"):
        LlmOutput.from_json({"type": "text", "value": "hello"})


def test_llm_request_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="input must not be empty"):
        LlmRequest(
            request_id="translate-test",
            workflow="translate",
            instructions="Return JSON.",
            input=[],
            output=JsonSchemaOutput(name="output", schema={}),
        )


def test_llm_request_rejects_invalid_scalar_fields() -> None:
    with pytest.raises(ValueError, match="request_id must not be empty"):
        LlmRequest(
            request_id=" ",
            workflow="translate",
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
        )

    with pytest.raises(ValueError, match="request_id must be a string"):
        LlmRequest(
            request_id=cast(str, None),
            workflow="translate",
            instructions="Return JSON.",
            input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
            output=JsonSchemaOutput(name="output", schema={}),
        )

def test_llm_request_rejects_duplicate_capabilities() -> None:
    with pytest.raises(ValueError, match="capabilities must be unique"):
        LlmRequest(
            request_id="translate-test",
            workflow="translate",
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


def test_pricing_and_cost_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="currency must be USD"):
        LlmPricing("EUR", "api_equivalent", 5.0, 0.5, 30.0)

    with pytest.raises(ValueError, match="basis must be api_equivalent"):
        LlmPricing("USD", "invoice", 5.0, 0.5, 30.0)

    with pytest.raises(ValueError, match="input_price_per_million"):
        LlmPricing("USD", "api_equivalent", -1, 0.5, 30.0)

    with pytest.raises(ValueError, match="amount"):
        LlmCostEstimate("USD", "api_equivalent", -1, 5.0, 0.5, 30.0)

    with pytest.raises(ValueError, match="currency must be USD"):
        LlmCostEstimate("EUR", "api_equivalent", 0, 5.0, 0.5, 30.0)

    with pytest.raises(ValueError, match="basis must be api_equivalent"):
        LlmCostEstimate("USD", "invoice", 0, 5.0, 0.5, 30.0)


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
