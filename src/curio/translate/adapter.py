import copy
import json
from collections.abc import Mapping
from typing import cast

from curio.config import LlmCallerPromptConfig
from curio.llm_caller import (
    JsonSchemaOutput,
    LlmCapability,
    LlmMessage,
    LlmMessageRole,
    LlmRequest,
    TextContentPart,
)
from curio.schemas import SchemaName, load_schema
from curio.translate.models import JsonObject, TranslationRequest

TRANSLATION_WORKFLOW = "translate"
TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME = "curio_translation_model_output"

DEFAULT_TRANSLATION_INSTRUCTIONS = (
    "Return only JSON that satisfies the provided schema. "
    "Classify each source block and conditionally translate it into English."
)
DEFAULT_TRANSLATION_USER_PROMPT_TEMPLATE = "\n".join(
    [
        "Use the translation request JSON below to classify language and conditionally translate each block into English.",
        "",
        "Rules:",
        "- Target language is exactly en.",
        "- Estimate english_confidence_estimate for each source block.",
        "- Set translation_required to false and translated_text to null only when the block is English above the threshold.",
        "- Otherwise set translation_required to true and translate the full source block into English.",
        "- Preserve source meaning; do not summarize or add interpretation.",
        "- Preserve URLs, code identifiers, hashtags, handles, filenames, and quoted strings unless natural language inside them clearly needs translation.",
        "- Preserve input block order and return exactly one output block for each input block.",
        "- Emit compact warnings only for corrupt text, partially untranslatable fragments, schema-repair events, mixed-language ambiguity, or provider/runtime issues.",
        "",
        "Translation request JSON:",
        "{translation_request_json}",
        "",
        "Required output JSON Schema:",
        "{output_schema_json}",
    ]
)


def translation_model_output_schema() -> JsonObject:
    response_schema = load_schema(SchemaName.TRANSLATION_RESPONSE)
    response_properties = cast(JsonObject, response_schema["properties"])
    response_defs = cast(JsonObject, response_schema["$defs"])
    return copy.deepcopy(
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["request_id", "blocks"],
            "properties": {
                "request_id": response_properties["request_id"],
                "blocks": response_properties["blocks"],
            },
            "$defs": {
                "warnings": response_defs["warnings"],
                "translatedBlock": response_defs["translatedBlock"],
            },
        }
    )


def build_translation_template_values(request: TranslationRequest) -> Mapping[str, object]:
    return {
        "translation_request_json": json.dumps(request.to_json(), ensure_ascii=False, indent=2, sort_keys=True),
        "output_schema_json": json.dumps(translation_model_output_schema(), ensure_ascii=False, indent=2, sort_keys=True),
        "request_id": request.request_id,
        "target_language": request.target_language,
        "english_confidence_threshold": request.english_confidence_threshold,
    }


def build_translation_instructions(
    request: TranslationRequest,
    prompt_config: LlmCallerPromptConfig | None = None,
) -> str:
    template = (
        DEFAULT_TRANSLATION_INSTRUCTIONS
        if prompt_config is None or prompt_config.instructions is None
        else prompt_config.instructions
    )
    return template.format(**build_translation_template_values(request))


def build_translation_prompt(
    request: TranslationRequest,
    prompt_config: LlmCallerPromptConfig | None = None,
) -> str:
    template = (
        DEFAULT_TRANSLATION_USER_PROMPT_TEMPLATE if prompt_config is None or prompt_config.user is None else prompt_config.user
    )
    return template.format(**build_translation_template_values(request))


def build_translation_llm_request(
    request: TranslationRequest,
    prompt_config: LlmCallerPromptConfig | None = None,
) -> LlmRequest:
    return LlmRequest(
        request_id=request.request_id,
        workflow=TRANSLATION_WORKFLOW,
        instructions=build_translation_instructions(request, prompt_config),
        input=[
            LlmMessage(
                role=LlmMessageRole.USER,
                content=[TextContentPart(text=build_translation_prompt(request, prompt_config))],
            )
        ],
        output=JsonSchemaOutput(
            name=TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME,
            schema=translation_model_output_schema(),
            strict=True,
        ),
        required_capabilities=(
            LlmCapability.TEXT_GENERATION,
            LlmCapability.JSON_SCHEMA_OUTPUT,
        ),
        metadata={
            "source": "curio.translate",
            "llm_caller": request.llm_caller,
        },
    )
