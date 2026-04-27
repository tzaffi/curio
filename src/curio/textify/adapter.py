import json
from collections.abc import Mapping

from curio.config import LlmCallerPromptConfig
from curio.llm_caller import (
    JsonSchemaOutput,
    LlmCapability,
    LlmMessage,
    LlmMessageRole,
    LlmRequest,
    LocalFileContentPart,
    TextContentPart,
)
from curio.textify.media import (
    effective_mime_type,
    preferred_output_hint,
    source_sha256,
)
from curio.textify.models import Artifact, JsonObject, TextifyRequest

TEXTIFY_WORKFLOW = "textify"
TEXTIFY_MODEL_OUTPUT_SCHEMA_NAME = "curio_textify_model_output"
SUGGESTED_FILE_POLICY = (
    "Suggest safe relative output paths. Preserve visible filenames exactly. "
    "Infer natural extensions for code, config, logs, and flat text. Split multiple implied files into separate records."
)
DEFAULT_TEXTIFY_INSTRUCTIONS = (
    "Return only JSON that satisfies the provided schema. Extract source-language text from the supplied local media."
)
DEFAULT_TEXTIFY_USER_PROMPT_TEMPLATE = "\n".join(
    [
        "Use the media artifact listed below to extract visible/readable source-language text.",
        "",
        "Rules:",
        "- Do not translate.",
        "- Do not summarize or interpret.",
        "- Preserve reading order and meaningful line breaks.",
        "- Use Markdown for headings, lists, tables, and document structure.",
        "- Use plain text or a natural code/config/log extension when the source is a flat file screenshot.",
        "- Suggest one or more safe relative output paths.",
        "- Preserve visible filenames exactly and infer extensions only when obvious.",
        "- Split multiple implied files into separate suggested file records.",
        "- Emit compact warnings for uncertain OCR, low quality, cropped/rotated content, or unreadable regions.",
        "",
        "Preferred output format: {preferred_output_format}",
        "Suggested file policy: {suggested_file_policy}",
        "",
        "Artifact manifest JSON:",
        "{artifact_manifest_json}",
        "",
        "Textify request JSON:",
        "{textify_request_json}",
        "",
        "Required output JSON Schema:",
        "{output_schema_json}",
    ]
)


def textify_model_output_schema() -> JsonObject:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["request_id", "artifacts"],
        "properties": {
            "request_id": {"type": "string", "minLength": 1},
            "artifacts": {
                "type": "array",
                "minItems": 1,
                "items": {"$ref": "#/$defs/modelArtifact"},
            },
        },
        "$defs": {
            "warnings": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "uniqueItems": True,
            },
            "suggestedFile": {
                "type": "object",
                "additionalProperties": False,
                "required": ["suggested_path", "output_format", "text"],
                "properties": {
                    "suggested_path": {"type": "string", "minLength": 1},
                    "output_format": {"type": "string", "minLength": 1},
                    "text": {"type": "string", "minLength": 1},
                },
            },
            "modelArtifact": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "artifact_id",
                    "name",
                    "status",
                    "suggested_files",
                    "detected_languages",
                    "page_count",
                    "warnings",
                ],
                "properties": {
                    "artifact_id": {"type": "integer", "minimum": 1},
                    "name": {"type": "string", "minLength": 1},
                    "status": {
                        "type": "string",
                        "enum": ["converted", "no_text_found"],
                    },
                    "suggested_files": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/suggestedFile"},
                    },
                    "detected_languages": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "uniqueItems": True,
                    },
                    "page_count": {
                        "oneOf": [
                            {"type": "number", "minimum": 0},
                            {"type": "null"},
                        ]
                    },
                    "warnings": {"$ref": "#/$defs/warnings"},
                },
            },
        },
    }


def artifact_manifest(artifact: Artifact, preferred_format: str) -> JsonObject:
    return {
        "artifact_id": artifact.artifact_id,
        "name": artifact.name,
        "path": artifact.path,
        "mime_type": effective_mime_type(artifact),
        "sha256": source_sha256(artifact),
        "source_language_hint": artifact.source_language_hint,
        "preferred_output_format": preferred_format,
        "context": dict(artifact.context),
    }


def build_textify_template_values(request: TextifyRequest, artifact: Artifact) -> Mapping[str, object]:
    preferred_format = preferred_output_hint(artifact, request.preferred_output_format)
    manifest = artifact_manifest(artifact, preferred_format)
    single_artifact_request = TextifyRequest(
        request_id=request.request_id,
        artifacts=[artifact],
        preferred_output_format=request.preferred_output_format,
        llm_caller=request.llm_caller,
    )
    return {
        "textify_request_json": json.dumps(
            single_artifact_request.to_json(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "output_schema_json": json.dumps(textify_model_output_schema(), ensure_ascii=False, indent=2, sort_keys=True),
        "request_id": request.request_id,
        "preferred_output_format": preferred_format,
        "artifact_manifest_json": json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        "suggested_file_policy": SUGGESTED_FILE_POLICY,
    }


def build_textify_instructions(
    request: TextifyRequest,
    artifact: Artifact,
    prompt_config: LlmCallerPromptConfig | None = None,
) -> str:
    template = DEFAULT_TEXTIFY_INSTRUCTIONS if prompt_config is None or prompt_config.instructions is None else prompt_config.instructions
    return template.format(**build_textify_template_values(request, artifact))


def build_textify_prompt(
    request: TextifyRequest,
    artifact: Artifact,
    prompt_config: LlmCallerPromptConfig | None = None,
) -> str:
    template = DEFAULT_TEXTIFY_USER_PROMPT_TEMPLATE if prompt_config is None or prompt_config.user is None else prompt_config.user
    return template.format(**build_textify_template_values(request, artifact))


def build_textify_llm_request(
    request: TextifyRequest,
    artifact: Artifact,
    prompt_config: LlmCallerPromptConfig | None = None,
) -> LlmRequest:
    mime_type = effective_mime_type(artifact) or "application/octet-stream"
    sha256 = source_sha256(artifact)
    preferred_format = preferred_output_hint(artifact, request.preferred_output_format)
    return LlmRequest(
        request_id=request.request_id,
        workflow=TEXTIFY_WORKFLOW,
        instructions=build_textify_instructions(request, artifact, prompt_config),
        input=[
            LlmMessage(
                role=LlmMessageRole.USER,
                content=[
                    TextContentPart(text=build_textify_prompt(request, artifact, prompt_config)),
                    LocalFileContentPart(
                        path=artifact.path,
                        mime_type=mime_type,
                        sha256=sha256,
                        name=artifact.name,
                    ),
                ],
            )
        ],
        output=JsonSchemaOutput(
            name=TEXTIFY_MODEL_OUTPUT_SCHEMA_NAME,
            schema=textify_model_output_schema(),
            strict=True,
        ),
        required_capabilities=_required_capabilities(mime_type),
        metadata={
            "source": "curio.textify",
            "llm_caller": request.llm_caller,
            "artifact_id": artifact.artifact_id,
            "artifact_name": artifact.name,
            "preferred_output_format": preferred_format,
            "suggested_path": _default_suggested_path(artifact, preferred_format),
        },
    )


def _required_capabilities(mime_type: str) -> tuple[LlmCapability, ...]:
    capabilities = [
        LlmCapability.JSON_SCHEMA_OUTPUT,
        LlmCapability.FILE_INPUT,
        LlmCapability.OCR,
        LlmCapability.SUGGESTED_FILE_OUTPUT,
        LlmCapability.RELATIVE_PATH_OUTPUT,
    ]
    if mime_type.startswith("image/"):
        capabilities.append(LlmCapability.IMAGE_INPUT)
    if mime_type == "application/pdf":
        capabilities.append(LlmCapability.PDF_INPUT)
    return tuple(capabilities)


def _default_suggested_path(artifact: Artifact, preferred_format: str) -> str:
    stem = artifact.name.rsplit(".", 1)[0] or "artifact"
    extension = "txt" if preferred_format == "txt" else "md"
    return f"{stem}.{extension}"
