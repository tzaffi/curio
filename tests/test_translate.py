from collections.abc import Sequence
from typing import cast

import pytest

import curio.translate as translate
from curio.config import LlmCallerPromptConfig
from curio.llm_caller import (
    LlmCostEstimate,
    LlmOutput,
    LlmPricing,
    LlmRequest,
    LlmResponse,
    LlmUsage,
    MeteredObject,
)
from curio.schemas import SchemaName, SchemaValidationError, validate_json
from curio.translate import (
    Block,
    LlmSummary,
    TranslatedBlock,
    TranslationRequest,
    TranslationRequestError,
    TranslationResponse,
    TranslationResponseError,
    TranslationService,
    counts_as_english,
)


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=100,
        cached_input_tokens=80,
        output_tokens=20,
        reasoning_tokens=None,
        total_tokens=120,
        metered_objects=[MeteredObject(name="request", quantity=1, unit="count")],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:01Z",
        wall_seconds=1,
        thinking_seconds=None,
    )


def make_block(block_id: int = 1) -> Block:
    return Block(
        block_id=block_id,
        name="tweet_text",
        source_language_hint="ja",
        text="今日は新しいモデルを公開します。",
        context={"artifact_kind": "tweet_json"},
    )


def make_request() -> TranslationRequest:
    return TranslationRequest(
        request_id="translate-test",
        blocks=[make_block()],
        llm_caller="translator_codex_gpt_55",
    )


def make_summary() -> LlmSummary:
    return LlmSummary(provider="codex_cli", model="gpt-test", usage=make_usage())


def make_cost_estimate() -> LlmCostEstimate:
    return LlmCostEstimate(
        currency="USD",
        basis="api_equivalent",
        amount=0.0002115,
        input_price_per_million=0.75,
        cached_input_price_per_million=0.075,
        output_price_per_million=4.5,
    )


class RecordingLlmClient:
    def __init__(self, response: LlmResponse) -> None:
        self.response = response
        self.requests: list[LlmRequest] = []

    def complete(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return self.response


def make_llm_response(
    output_value: object,
    *,
    warnings: Sequence[str] = (),
    request_id: str = "translate-test",
) -> LlmResponse:
    return LlmResponse(
        request_id=request_id,
        status="succeeded",
        provider="codex_cli",
        model="gpt-test",
        output=LlmOutput(value=output_value),
        usage=make_usage(),
        warnings=warnings,
    )


def test_translate_root_exports_public_service_contracts() -> None:
    assert translate.__all__ == [
        "DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD",
        "DEFAULT_TARGET_LANGUAGE",
        "TRANSLATION_REQUEST_VERSION",
        "TRANSLATION_RESPONSE_VERSION",
        "Block",
        "LlmSummary",
        "TranslatedBlock",
        "TranslationError",
        "TranslationRequest",
        "TranslationRequestError",
        "TranslationResponse",
        "TranslationResponseError",
        "TranslationService",
        "counts_as_english",
    ]


def test_counts_as_english_requires_language_and_threshold() -> None:
    assert counts_as_english("en-US", 0.91, 0.9) is True
    assert counts_as_english("en", 0.89, 0.9) is False
    assert counts_as_english("fr", 0.99, 0.9) is False


def test_counts_as_english_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="detected_language must not be empty"):
        counts_as_english(" ", 0.9, 0.9)

    with pytest.raises(ValueError, match="english_confidence must be a number between 0 and 1"):
        counts_as_english("en", -0.1, 0.9)

    with pytest.raises(ValueError, match="english_confidence must be a number between 0 and 1"):
        counts_as_english("en", cast(float, True), 0.9)


def test_translation_request_serializes_to_schema_payload() -> None:
    request = make_request()

    payload = request.to_json()

    assert request.llm_caller == "translator_codex_gpt_55"
    assert payload["translation_request_version"] == "curio-translation-request.v1"
    assert payload["blocks"][0]["context"] == {"artifact_kind": "tweet_json"}
    validate_json(payload, SchemaName.TRANSLATION_REQUEST)


def test_translation_request_parses_from_schema_payload() -> None:
    payload = make_request().to_json()

    request = TranslationRequest.from_json(payload)

    assert request == make_request()


def test_translation_request_from_json_rejects_schema_invalid_payload() -> None:
    payload = make_request().to_json()
    payload["target_language"] = "fr"

    with pytest.raises(SchemaValidationError, match="translation_request"):
        TranslationRequest.from_json(payload)


def test_translation_request_preserves_accepted_string_values() -> None:
    request = TranslationRequest(
        request_id=" translate-test ",
        blocks=[
            Block(
                block_id=1,
                name=" tweet_text ",
                source_language_hint=" ja ",
                text=" text with intentional spacing ",
            )
        ],
    )

    payload = request.to_json()

    assert payload["request_id"] == " translate-test "
    assert payload["blocks"][0]["name"] == " tweet_text "
    assert payload["blocks"][0]["source_language_hint"] == " ja "
    assert payload["blocks"][0]["text"] == " text with intentional spacing "


def test_translation_response_serializes_to_schema_payload() -> None:
    response = TranslationResponse(
        request_id="translate-test",
        blocks=[
            TranslatedBlock(
                block_id=1,
                name="tweet_text",
                detected_language="ja",
                english_confidence_estimate=0.01,
                translation_required=True,
                translated_text="Today we are releasing a new model.",
                warnings=[],
            )
        ],
        llm=make_summary(),
        warnings=["request warning"],
    )

    payload = response.to_json()

    assert payload["llm"]["provider"] == "codex_cli"
    assert payload["llm"]["cost_estimate"] is None
    assert payload["blocks"][0]["translated_text"] == "Today we are releasing a new model."
    validate_json(payload, SchemaName.TRANSLATION_RESPONSE)


def test_translation_response_serializes_cost_estimate_to_schema_payload() -> None:
    response = TranslationResponse(
        request_id="translate-test",
        blocks=[
            TranslatedBlock(
                block_id=1,
                name="tweet_text",
                detected_language="ja",
                english_confidence_estimate=0.01,
                translation_required=True,
                translated_text="Today we are releasing a new model.",
            )
        ],
        llm=LlmSummary(
            provider="codex_cli",
            model="gpt-test",
            usage=make_usage(),
            cost_estimate=make_cost_estimate(),
        ),
    )

    payload = response.to_json()

    assert payload["llm"]["cost_estimate"] == make_cost_estimate().to_json()
    validate_json(payload, SchemaName.TRANSLATION_RESPONSE)
    assert TranslationResponse.from_json(payload) == response


def test_translation_response_parses_from_schema_payload() -> None:
    response = TranslationResponse(
        request_id="translate-test",
        blocks=[
            TranslatedBlock(
                block_id=1,
                name="tweet_text",
                detected_language="ja",
                english_confidence_estimate=0.01,
                translation_required=True,
                translated_text="Today we are releasing a new model.",
            )
        ],
        llm=make_summary(),
        warnings=["request warning"],
    )

    assert TranslationResponse.from_json(response.to_json()) == response


def test_translation_response_schema_rejects_google_document_ai_provider() -> None:
    payload = TranslationResponse(
        request_id="translate-test",
        blocks=[
            TranslatedBlock(
                block_id=1,
                name="tweet_text",
                detected_language="ja",
                english_confidence_estimate=0.01,
                translation_required=True,
                translated_text="Today we are releasing a new model.",
            )
        ],
        llm=make_summary(),
    ).to_json()
    payload["llm"]["provider"] = "google_document_ai"

    with pytest.raises(SchemaValidationError, match="translation_response"):
        validate_json(payload, SchemaName.TRANSLATION_RESPONSE)

    with pytest.raises(SchemaValidationError, match="translation_response"):
        TranslationResponse.from_json(payload)


def test_english_translated_block_serializes_to_null_translation() -> None:
    block = TranslatedBlock(
        block_id=1,
        name="tweet_text",
        detected_language="en",
        english_confidence_estimate=0.99,
        translation_required=False,
        translated_text=None,
    )

    assert block.to_json()["translated_text"] is None


def test_translation_nested_models_parse_from_json() -> None:
    assert Block.from_json(make_block().to_json()) == make_block()
    assert TranslatedBlock.from_json(
        {
            "block_id": 1,
            "name": "tweet_text",
            "detected_language": "en",
            "english_confidence_estimate": 0.99,
            "translation_required": False,
            "translated_text": None,
            "warnings": [],
        }
    ) == TranslatedBlock(
        block_id=1,
        name="tweet_text",
        detected_language="en",
        english_confidence_estimate=0.99,
        translation_required=False,
        translated_text=None,
    )
    assert LlmSummary.from_json(make_summary().to_json()) == make_summary()


def test_translation_nested_parsers_reject_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="block_id is required"):
        Block.from_json({"name": "tweet_text", "source_language_hint": None, "text": "hello"})

    with pytest.raises(ValueError, match="context must be an object"):
        Block.from_json(
            {
                "block_id": 1,
                "name": "tweet_text",
                "source_language_hint": None,
                "text": "hello",
                "context": [],
            }
        )

    with pytest.raises(ValueError, match="translation_required must be a boolean"):
        TranslatedBlock.from_json(
            {
                "block_id": 1,
                "name": "tweet_text",
                "detected_language": "ja",
                "english_confidence_estimate": 0.01,
                "translation_required": 1,
                "translated_text": "Translated text.",
                "warnings": [],
            }
        )

    with pytest.raises(ValueError, match="warnings must be a list"):
        TranslatedBlock.from_json(
            {
                "block_id": 1,
                "name": "tweet_text",
                "detected_language": "ja",
                "english_confidence_estimate": 0.01,
                "translation_required": True,
                "translated_text": "Translated text.",
                "warnings": {},
            }
        )


def test_block_rejects_invalid_fields() -> None:
    with pytest.raises(ValueError, match="block_id must be a positive integer"):
        Block(block_id=0, name="tweet_text", source_language_hint=None, text="")

    with pytest.raises(ValueError, match="block_id must be a positive integer"):
        Block(block_id=False, name="tweet_text", source_language_hint=None, text="text")

    with pytest.raises(ValueError, match="source_language_hint must not be empty"):
        Block(block_id=1, name="tweet_text", source_language_hint="", text="")

    with pytest.raises(ValueError, match="text must not be empty"):
        Block(block_id=1, name="tweet_text", source_language_hint=None, text=" ")

    with pytest.raises(ValueError, match="context must be an object"):
        Block(block_id=1, name="tweet_text", source_language_hint=None, text="text", context=cast(dict[str, object], []))


def test_translation_request_rejects_invalid_fields() -> None:
    with pytest.raises(TranslationRequestError, match="target_language must be en"):
        TranslationRequest(request_id="translate-test", blocks=[make_block()], target_language="fr")

    with pytest.raises(TranslationRequestError, match="blocks must not be empty"):
        TranslationRequest(request_id="translate-test", blocks=[])

    with pytest.raises(TranslationRequestError, match="block_id values must be unique"):
        TranslationRequest(request_id="translate-test", blocks=[make_block(1), make_block(1)])

    with pytest.raises(ValueError, match="request_id must be a string"):
        TranslationRequest(request_id=cast(str, None), blocks=[make_block()])

    with pytest.raises(ValueError, match="llm_caller must not be empty"):
        TranslationRequest(request_id="translate-test", blocks=[make_block()], llm_caller=" ")


def test_translated_block_rejects_inconsistent_translation_state() -> None:
    with pytest.raises(TranslationResponseError, match="translated_text is required"):
        TranslatedBlock(
            block_id=1,
            name="tweet_text",
            detected_language="ja",
            english_confidence_estimate=0.01,
            translation_required=True,
            translated_text=None,
        )

    with pytest.raises(TranslationResponseError, match="translated_text must be null"):
        TranslatedBlock(
            block_id=1,
            name="tweet_text",
            detected_language="en",
            english_confidence_estimate=0.99,
            translation_required=False,
            translated_text="Already English.",
        )

    with pytest.raises(ValueError, match="translated_text must not be empty"):
        TranslatedBlock(
            block_id=1,
            name="tweet_text",
            detected_language="ja",
            english_confidence_estimate=0.01,
            translation_required=True,
            translated_text="",
        )

    with pytest.raises(ValueError, match="english_confidence_estimate must be a number between 0 and 1"):
        TranslatedBlock(
            block_id=1,
            name="tweet_text",
            detected_language="ja",
            english_confidence_estimate=cast(float, True),
            translation_required=True,
            translated_text="Translated text.",
        )

    with pytest.raises(ValueError, match="warnings must be unique"):
        TranslatedBlock(
            block_id=1,
            name="tweet_text",
            detected_language="ja",
            english_confidence_estimate=0.01,
            translation_required=True,
            translated_text="Translated text.",
            warnings=["same", "same"],
        )


def test_translation_response_rejects_invalid_fields() -> None:
    translated_block = TranslatedBlock(
        block_id=1,
        name="tweet_text",
        detected_language="en",
        english_confidence_estimate=0.99,
        translation_required=False,
        translated_text=None,
    )

    with pytest.raises(TranslationResponseError, match="target_language must be en"):
        TranslationResponse(
            request_id="translate-test",
            blocks=[translated_block],
            llm=make_summary(),
            target_language="fr",
        )

    with pytest.raises(TranslationResponseError, match="blocks must not be empty"):
        TranslationResponse(request_id="translate-test", blocks=[], llm=make_summary())


def test_llm_summary_rejects_empty_model() -> None:
    with pytest.raises(ValueError, match="model must not be empty"):
        LlmSummary(provider="codex_cli", model="", usage=make_usage())


def test_llm_summary_rejects_google_document_ai_provider() -> None:
    with pytest.raises(TranslationResponseError, match="google_document_ai is not a valid translation"):
        LlmSummary(provider="google_document_ai", model="document-ai-layout-parser", usage=make_usage())


def test_translation_service_calls_injected_llm_client_and_assembles_response() -> None:
    client = RecordingLlmClient(
        make_llm_response(
            {
                "request_id": "translate-test",
                "blocks": [
                    {
                        "block_id": 1,
                        "name": "tweet_text",
                        "detected_language": "ja",
                        "english_confidence_estimate": 0.01,
                        "translation_required": True,
                        "translated_text": "Today we are releasing a new model.",
                        "warnings": ["partial nuance warning"],
                    }
                ],
            },
            warnings=["provider warning"],
        )
    )
    service = TranslationService(llm_client=client)

    response = service.translate(make_request())

    assert len(client.requests) == 1
    assert client.requests[0].request_id == "translate-test"
    assert client.requests[0].workflow == "translate"
    assert response == TranslationResponse(
        request_id="translate-test",
        blocks=[
            TranslatedBlock(
                block_id=1,
                name="tweet_text",
                detected_language="ja",
                english_confidence_estimate=0.01,
                translation_required=True,
                translated_text="Today we are releasing a new model.",
                warnings=["partial nuance warning"],
            )
        ],
        llm=LlmSummary(provider="codex_cli", model="gpt-test", usage=make_usage()),
        warnings=["provider warning"],
    )


def test_translation_service_adds_cost_estimate_when_pricing_is_configured() -> None:
    client = RecordingLlmClient(
        make_llm_response(
            {
                "request_id": "translate-test",
                "blocks": [
                    {
                        "block_id": 1,
                        "name": "tweet_text",
                        "detected_language": "ja",
                        "english_confidence_estimate": 0.01,
                        "translation_required": True,
                        "translated_text": "Today we are releasing a new model.",
                        "warnings": [],
                    }
                ],
            }
        )
    )

    response = TranslationService(
        llm_client=client,
        pricing_config=LlmPricing("USD", "api_equivalent", 0.75, 0.075, 4.5),
    ).translate(make_request())

    assert response.llm.cost_estimate == LlmCostEstimate("USD", "api_equivalent", 0.000171, 0.75, 0.075, 4.5)


def test_translation_service_passes_prompt_config_to_adapter() -> None:
    client = RecordingLlmClient(
        make_llm_response(
            {
                "request_id": "translate-test",
                "blocks": [
                    {
                        "block_id": 1,
                        "name": "tweet_text",
                        "detected_language": "ja",
                        "english_confidence_estimate": 0.01,
                        "translation_required": True,
                        "translated_text": "Today we are releasing a new model.",
                        "warnings": [],
                    }
                ],
            }
        )
    )
    service = TranslationService(
        llm_client=client,
        prompt_config=LlmCallerPromptConfig(instructions="Service prompt {request_id}", user="User {target_language}"),
    )

    service.translate(make_request())

    assert client.requests[0].instructions == "Service prompt translate-test"
    assert client.requests[0].input[0].content[0].text == "User en"


def test_translation_service_propagates_validation_errors() -> None:
    client = RecordingLlmClient(
        make_llm_response(
            {
                "request_id": "translate-test",
                "blocks": [
                    {
                        "block_id": 1,
                        "name": "tweet_text",
                        "detected_language": "en",
                        "english_confidence_estimate": 0.99,
                        "translation_required": True,
                        "translated_text": "Should not translate.",
                        "warnings": [],
                    }
                ],
            }
        )
    )

    with pytest.raises(TranslationResponseError, match="counts as English"):
        TranslationService(llm_client=client).translate(make_request())
