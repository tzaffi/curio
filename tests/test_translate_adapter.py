import json

from curio.llm_caller import LlmCapability, LlmMessageRole
from curio.schemas import SchemaName, load_schema, validate_json
from curio.translate import Block, TranslationRequest
from curio.translate.adapter import (
    DEFAULT_TRANSLATION_TIMEOUT_SECONDS,
    TRANSLATION_INSTRUCTIONS,
    TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME,
    TRANSLATION_WORKFLOW,
    build_translation_llm_request,
    build_translation_prompt,
    translation_model_output_schema,
)


def make_request(
    *,
    provider: str | None = "codex_cli",
    model: str | None = "gpt-test",
    timeout_seconds: int | None = 120,
) -> TranslationRequest:
    return TranslationRequest(
        request_id="translate-test",
        blocks=[
            Block(
                block_id=1,
                name="tweet_text",
                source_language_hint="ja",
                text="今日は新しいモデルを公開します。",
                context={"artifact_kind": "tweet_json"},
            )
        ],
        provider=provider,
        model=model,
        timeout_seconds=timeout_seconds,
    )


def test_translation_model_output_schema_is_derived_from_public_response_schema() -> None:
    schema = translation_model_output_schema()
    public_schema = load_schema(SchemaName.TRANSLATION_RESPONSE)

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["request_id", "blocks"]
    assert schema["properties"]["request_id"] == public_schema["properties"]["request_id"]
    assert schema["properties"]["blocks"] == public_schema["properties"]["blocks"]
    assert schema["$defs"]["warnings"] == public_schema["$defs"]["warnings"]
    assert schema["$defs"]["translatedBlock"] == public_schema["$defs"]["translatedBlock"]
    assert "llm" not in schema["properties"]


def test_build_translation_prompt_embeds_request_and_output_schema() -> None:
    request = make_request()

    prompt = build_translation_prompt(request)

    assert "conditionally translate each block into English" in prompt
    assert "do not summarize" in prompt
    assert "今日は新しいモデルを公開します。" in prompt
    assert '"english_confidence_threshold": 0.9' in prompt
    assert '"translatedBlock"' in prompt
    assert json.dumps(request.to_json(), ensure_ascii=False, indent=2, sort_keys=True) in prompt
    assert json.dumps(translation_model_output_schema(), ensure_ascii=False, indent=2, sort_keys=True) in prompt


def test_build_translation_llm_request_maps_translation_request() -> None:
    request = make_request()

    llm_request = build_translation_llm_request(request)
    payload = llm_request.to_json()

    assert llm_request.request_id == "translate-test"
    assert llm_request.workflow == TRANSLATION_WORKFLOW
    assert llm_request.model == "gpt-test"
    assert llm_request.instructions == TRANSLATION_INSTRUCTIONS
    assert llm_request.required_capabilities == (
        LlmCapability.TEXT_GENERATION,
        LlmCapability.JSON_SCHEMA_OUTPUT,
    )
    assert llm_request.timeout_seconds == 120
    assert llm_request.metadata == {
        "source": "curio.translate",
        "provider": "codex_cli",
    }
    assert llm_request.input[0].role == LlmMessageRole.USER
    assert llm_request.input[0].content[0].text == build_translation_prompt(request)
    assert llm_request.output.name == TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME
    assert llm_request.output.schema == translation_model_output_schema()
    assert llm_request.output.strict is True
    validate_json(payload, SchemaName.LLM_REQUEST)


def test_build_translation_llm_request_uses_default_timeout_and_preserves_nulls() -> None:
    request = make_request(provider=None, model=None, timeout_seconds=None)

    llm_request = build_translation_llm_request(request)

    assert llm_request.model is None
    assert llm_request.timeout_seconds == DEFAULT_TRANSLATION_TIMEOUT_SECONDS
    assert llm_request.metadata == {
        "source": "curio.translate",
        "provider": None,
    }
