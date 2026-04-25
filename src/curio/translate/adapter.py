import copy
import json
from typing import cast

from curio.llm_caller import (
    JsonSchemaOutput,
    LlmCapability,
    LlmMessage,
    LlmMessageRole,
    LlmRequest,
    ProviderName,
    TextContentPart,
)
from curio.schemas import SchemaName, load_schema
from curio.translate.models import JsonObject, TranslationRequest

TRANSLATION_WORKFLOW = "translate"
TRANSLATION_MODEL_OUTPUT_SCHEMA_NAME = "curio_translation_model_output"
DEFAULT_TRANSLATION_TIMEOUT_SECONDS = 300

TRANSLATION_INSTRUCTIONS = (
    "Return only JSON that satisfies the provided schema. "
    "Classify each source block and conditionally translate it into English."
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


def build_translation_prompt(request: TranslationRequest) -> str:
    request_json = json.dumps(request.to_json(), ensure_ascii=False, indent=2, sort_keys=True)
    schema_json = json.dumps(translation_model_output_schema(), ensure_ascii=False, indent=2, sort_keys=True)
    return "\n".join(
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
            request_json,
            "",
            "Required output JSON Schema:",
            schema_json,
        ]
    )


def build_translation_llm_request(request: TranslationRequest) -> LlmRequest:
    provider = None if request.provider is None else cast(ProviderName, request.provider).value
    return LlmRequest(
        request_id=request.request_id,
        workflow=TRANSLATION_WORKFLOW,
        model=request.model,
        instructions=TRANSLATION_INSTRUCTIONS,
        input=[
            LlmMessage(
                role=LlmMessageRole.USER,
                content=[TextContentPart(text=build_translation_prompt(request))],
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
        timeout_seconds=request.timeout_seconds or DEFAULT_TRANSLATION_TIMEOUT_SECONDS,
        metadata={
            "source": "curio.translate",
            "provider": provider,
        },
    )
