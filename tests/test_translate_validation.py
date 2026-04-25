import pytest

import curio.translate.validation as validation
from curio.llm_caller import (
    LlmOutput,
    LlmResponse,
    LlmStatus,
    LlmUsage,
    MeteredObject,
    ProviderName,
)
from curio.translate import (
    Block,
    TranslatedBlock,
    TranslationRequest,
    TranslationResponseError,
)
from curio.translate.validation import (
    translated_blocks_from_llm_response,
    validate_translated_blocks,
    validate_translation_model_output,
)


def make_request() -> TranslationRequest:
    return TranslationRequest(
        request_id="translate-test",
        blocks=[
            Block(
                block_id=1,
                name="tweet_text",
                source_language_hint="ja",
                text="今日は新しいモデルを公開します。",
            ),
            Block(
                block_id=2,
                name="page_main_text",
                source_language_hint=None,
                text="Already English.",
            ),
        ],
    )


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=100,
        cached_input_tokens=None,
        output_tokens=20,
        reasoning_tokens=None,
        total_tokens=120,
        metered_objects=[MeteredObject(name="request", quantity=1, unit="count")],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:01Z",
        wall_seconds=1,
        thinking_seconds=None,
    )


def make_output_value(*, blocks: list[dict[str, object]] | None = None, request_id: str = "translate-test") -> dict[str, object]:
    return {
        "request_id": request_id,
        "blocks": blocks
        if blocks is not None
        else [
            {
                "block_id": 1,
                "name": "tweet_text",
                "detected_language": "ja",
                "english_confidence_estimate": 0.01,
                "translation_required": True,
                "translated_text": "Today we are releasing a new model.",
                "warnings": [],
            },
            {
                "block_id": 2,
                "name": "page_main_text",
                "detected_language": "en-US",
                "english_confidence_estimate": 0.99,
                "translation_required": False,
                "translated_text": None,
                "warnings": [],
            },
        ],
    }


def make_response(
    *,
    output_value: object | None = None,
    status: LlmStatus | str = LlmStatus.SUCCEEDED,
    request_id: str = "translate-test",
    output_is_none: bool = False,
) -> LlmResponse:
    return LlmResponse(
        request_id=request_id,
        status=status,
        provider=ProviderName.CODEX_CLI,
        model="gpt-test",
        output=None if output_is_none else LlmOutput(value=make_output_value() if output_value is None else output_value),
        usage=make_usage(),
    )


def test_translated_blocks_from_llm_response_returns_ordered_blocks() -> None:
    blocks = translated_blocks_from_llm_response(make_request(), make_response())

    assert blocks == (
        TranslatedBlock(
            block_id=1,
            name="tweet_text",
            detected_language="ja",
            english_confidence_estimate=0.01,
            translation_required=True,
            translated_text="Today we are releasing a new model.",
        ),
        TranslatedBlock(
            block_id=2,
            name="page_main_text",
            detected_language="en-US",
            english_confidence_estimate=0.99,
            translation_required=False,
            translated_text=None,
        ),
    )


def test_translated_blocks_from_llm_response_rejects_response_level_failures() -> None:
    request = make_request()

    with pytest.raises(TranslationResponseError, match="LLM response request_id must match"):
        translated_blocks_from_llm_response(request, make_response(request_id="other"))

    with pytest.raises(TranslationResponseError, match="status must be succeeded"):
        translated_blocks_from_llm_response(request, make_response(status=LlmStatus.FAILED))

    with pytest.raises(TranslationResponseError, match="output is required"):
        translated_blocks_from_llm_response(request, make_response(output_is_none=True))


def test_validate_translation_model_output_rejects_invalid_schema_shape() -> None:
    with pytest.raises(TranslationResponseError, match="schema validation"):
        validate_translation_model_output({"request_id": "translate-test", "blocks": []})

    with pytest.raises(TranslationResponseError, match="schema validation"):
        validate_translation_model_output(
            make_output_value(
                blocks=[
                    {
                        "block_id": 1,
                        "name": "tweet_text",
                        "detected_language": "en",
                        "english_confidence_estimate": 0.99,
                        "translation_required": False,
                        "translated_text": "Already English.",
                        "warnings": [],
                    }
                ]
            )
        )


def test_translated_blocks_from_llm_response_rejects_output_request_id_mismatch() -> None:
    with pytest.raises(TranslationResponseError, match="LLM output request_id must match"):
        translated_blocks_from_llm_response(make_request(), make_response(output_value=make_output_value(request_id="other")))


def test_validate_translated_blocks_rejects_duplicate_missing_extra_and_order_changes() -> None:
    request = make_request()

    with pytest.raises(TranslationResponseError, match="duplicate translated block ids: 1"):
        validate_translated_blocks(
            request,
            [
                TranslatedBlock(1, "tweet_text", "ja", 0.01, True, "Translated."),
                TranslatedBlock(1, "tweet_text", "ja", 0.01, True, "Translated again."),
            ],
        )

    with pytest.raises(TranslationResponseError, match="missing translated block ids: 2"):
        validate_translated_blocks(
            request,
            [TranslatedBlock(1, "tweet_text", "ja", 0.01, True, "Translated.")],
        )

    with pytest.raises(TranslationResponseError, match="unexpected translated block ids: 3"):
        validate_translated_blocks(
            request,
            [
                TranslatedBlock(1, "tweet_text", "ja", 0.01, True, "Translated."),
                TranslatedBlock(2, "page_main_text", "en", 0.99, False, None),
                TranslatedBlock(3, "extra", "en", 0.99, False, None),
            ],
        )

    with pytest.raises(TranslationResponseError, match="order must match"):
        validate_translated_blocks(
            request,
            [
                TranslatedBlock(2, "page_main_text", "en", 0.99, False, None),
                TranslatedBlock(1, "tweet_text", "ja", 0.01, True, "Translated."),
            ],
        )


def test_validate_translated_blocks_rejects_name_and_threshold_mismatches() -> None:
    request = make_request()

    with pytest.raises(TranslationResponseError, match="name must match"):
        validate_translated_blocks(
            request,
            [
                TranslatedBlock(1, "wrong_name", "ja", 0.01, True, "Translated."),
                TranslatedBlock(2, "page_main_text", "en", 0.99, False, None),
            ],
        )

    with pytest.raises(TranslationResponseError, match="counts as English"):
        validate_translated_blocks(
            request,
            [
                TranslatedBlock(1, "tweet_text", "en", 0.99, True, "Should not translate."),
                TranslatedBlock(2, "page_main_text", "en", 0.99, False, None),
            ],
        )

    with pytest.raises(TranslationResponseError, match="must require translation"):
        validate_translated_blocks(
            request,
            [
                TranslatedBlock(1, "tweet_text", "ja", 0.01, True, "Translated."),
                TranslatedBlock(2, "page_main_text", "en", 0.89, False, None),
            ],
        )


def test_translated_blocks_from_llm_response_rejects_non_object_output_value() -> None:
    with pytest.raises(TranslationResponseError, match="schema validation"):
        translated_blocks_from_llm_response(make_request(), make_response(output_value=[]))


def test_validation_local_helpers_report_defensive_shape_errors() -> None:
    with pytest.raises(TranslationResponseError, match="value must be an object"):
        validation._require_mapping([], "value")

    with pytest.raises(TranslationResponseError, match="value must be a list"):
        validation._require_list({}, "value")

    with pytest.raises(TranslationResponseError, match="missing is required"):
        validation._require_field({}, "missing")

    with pytest.raises(TranslationResponseError, match="value must be a string"):
        validation._require_string(None, "value")

    with pytest.raises(TranslationResponseError, match="value must not be empty"):
        validation._require_string(" ", "value")
