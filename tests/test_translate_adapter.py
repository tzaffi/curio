import json

from curio.config import LlmCallerPromptConfig
from curio.llm_caller import LlmCapability, LlmMessageRole
from curio.schemas import SchemaName, load_schema, validate_json
from curio.translate import Block, TranslationRequest
from curio.translate.adapter import (
    DEFAULT_TRANSLATION_INSTRUCTIONS,
    TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME,
    TRANSLATION_WORKFLOW,
    build_translation_instructions,
    build_translation_llm_request,
    build_translation_prompt,
    translation_model_output_schema,
)


def make_request(
    *,
    llm_caller: str | None = "translator_codex_gpt_55",
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
        llm_caller=llm_caller,
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


def test_build_translation_prompt_uses_custom_prompt_config() -> None:
    request = make_request()
    prompt_config = LlmCallerPromptConfig(
        instructions="Custom instructions for {request_id} in {target_language}",
        user=(
            "Custom user threshold {english_confidence_threshold}\n"
            "{translation_request_json}\n"
            "{output_schema_json}"
        ),
    )

    instructions = build_translation_instructions(request, prompt_config)
    prompt = build_translation_prompt(request, prompt_config)
    llm_request = build_translation_llm_request(request, prompt_config)

    assert instructions == "Custom instructions for translate-test in en"
    assert "Custom user threshold 0.9" in prompt
    assert json.dumps(request.to_json(), ensure_ascii=False, indent=2, sort_keys=True) in prompt
    assert json.dumps(translation_model_output_schema(), ensure_ascii=False, indent=2, sort_keys=True) in prompt
    assert llm_request.instructions == instructions
    assert llm_request.input[0].content[0].text == prompt


def test_build_translation_prompt_allows_partial_prompt_config() -> None:
    request = make_request()
    instructions_only = LlmCallerPromptConfig(instructions="Only {request_id}")
    user_only = LlmCallerPromptConfig(user="Only user {target_language}")

    assert build_translation_instructions(request, instructions_only) == "Only translate-test"
    assert build_translation_prompt(request, instructions_only) == build_translation_prompt(request)
    assert build_translation_instructions(request, user_only) == DEFAULT_TRANSLATION_INSTRUCTIONS
    assert build_translation_prompt(request, user_only) == "Only user en"


def test_build_translation_llm_request_maps_translation_request() -> None:
    request = make_request()

    llm_request = build_translation_llm_request(request)
    payload = llm_request.to_json()

    assert llm_request.request_id == "translate-test"
    assert llm_request.workflow == TRANSLATION_WORKFLOW
    assert llm_request.instructions == DEFAULT_TRANSLATION_INSTRUCTIONS
    assert llm_request.required_capabilities == (
        LlmCapability.TEXT_GENERATION,
        LlmCapability.JSON_SCHEMA_OUTPUT,
    )
    assert llm_request.metadata == {
        "source": "curio.translate",
        "llm_caller": "translator_codex_gpt_55",
    }
    assert llm_request.input[0].role == LlmMessageRole.USER
    assert llm_request.input[0].content[0].text == build_translation_prompt(request)
    assert llm_request.output.name == TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME
    assert llm_request.output.schema == translation_model_output_schema()
    assert llm_request.output.strict is True
    validate_json(payload, SchemaName.LLM_REQUEST)


def test_build_translation_llm_request_preserves_null_llm_caller_metadata() -> None:
    request = make_request(llm_caller=None)

    llm_request = build_translation_llm_request(request)

    assert llm_request.metadata == {
        "source": "curio.translate",
        "llm_caller": None,
    }
