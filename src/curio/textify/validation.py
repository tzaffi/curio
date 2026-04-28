from collections.abc import Mapping
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError

from curio.llm_caller import LlmResponse, LlmStatus
from curio.textify.adapter import textify_model_output_schema
from curio.textify.media import effective_mime_type, source_sha256
from curio.textify.models import (
    JsonValue,
    SuggestedTextFile,
    TextifiedSource,
    TextifyRequest,
    TextifyResponseError,
    TextifySource,
    TextifyStatus,
)

MARKDOWN_CODE_FENCE_REPAIR_WARNING = "removed single outer markdown code fence from model output"


def textified_source_from_llm_response(
    request: TextifyRequest,
    source: TextifySource,
    response: LlmResponse,
) -> TextifiedSource:
    if response.request_id != request.request_id:
        raise TextifyResponseError("LLM response request_id must match textify request_id")
    if response.status != LlmStatus.SUCCEEDED:
        raise TextifyResponseError("LLM response status must be succeeded")
    if response.output is None:
        raise TextifyResponseError("LLM response output is required")

    validate_textify_model_output(response.output.value)
    payload = _require_mapping(response.output.value, "LLM output value")
    output_request_id = _require_string(_require_field(payload, "request_id"), "request_id")
    if output_request_id != request.request_id:
        raise TextifyResponseError("LLM output request_id must match textify request_id")

    model_source = _model_source_from_json(_require_field(payload, "source"))
    model_source = _repair_textified_model_source(source, model_source)
    validate_textified_model_source(source, model_source)
    return _response_source_from_model(source, model_source)


def validate_textify_model_output(value: JsonValue) -> None:
    validator = Draft202012Validator(textify_model_output_schema(), format_checker=FormatChecker())
    try:
        validator.validate(value)
    except JsonSchemaLibraryError as exc:
        raise TextifyResponseError(f"LLM output failed textify schema validation: {exc.message}") from exc


def validate_textified_model_source(
    input_source: TextifySource,
    model_source: Mapping[str, JsonValue],
) -> None:
    model_source = _repair_textified_model_source(input_source, _model_source_from_json(model_source))
    if _require_string(_require_field(model_source, "name"), "name") != input_source.name:
        raise TextifyResponseError("textified source name must match input source name")
    status = TextifyStatus(_require_string(_require_field(model_source, "status"), "status"))
    suggested_files = [
        SuggestedTextFile.from_json(item)
        for item in _require_list(_require_field(model_source, "suggested_files"), "suggested_files")
    ]
    if status == TextifyStatus.CONVERTED and not suggested_files:
        raise TextifyResponseError("converted sources must include suggested_files")
    if status != TextifyStatus.CONVERTED and suggested_files:
        raise TextifyResponseError("non-converted sources must not include suggested_files")
    _require_list(_require_field(model_source, "warnings"), "warnings")
    _optional_non_negative_number(_require_field(model_source, "page_count"), "page_count")


def _response_source_from_model(
    input_source: TextifySource,
    model_source: Mapping[str, JsonValue],
) -> TextifiedSource:
    return TextifiedSource(
        name=input_source.name,
        input_mime_type=effective_mime_type(input_source),
        source_sha256=source_sha256(input_source),
        textification_required=True,
        status=TextifyStatus(_require_string(_require_field(model_source, "status"), "status")),
        suggested_files=[
            SuggestedTextFile.from_json(item)
            for item in _require_list(_require_field(model_source, "suggested_files"), "suggested_files")
        ],
        detected_languages=[
            _require_string(language, "language")
            for language in _require_list(_require_field(model_source, "detected_languages"), "detected_languages")
        ],
        page_count=_optional_non_negative_number(_require_field(model_source, "page_count"), "page_count"),
        warnings=[
            _require_string(warning, "warning")
            for warning in _require_list(_require_field(model_source, "warnings"), "warnings")
        ],
    )


def _model_source_from_json(value: object) -> Mapping[str, JsonValue]:
    return _require_mapping(value, "model source")


def _repair_textified_model_source(
    input_source: TextifySource,
    model_source: Mapping[str, JsonValue],
) -> Mapping[str, JsonValue]:
    suggested_files: list[JsonValue] = []
    warnings = [
        _require_string(warning, "warning")
        for warning in _require_list(_require_field(model_source, "warnings"), "warnings")
    ]
    for item in _require_list(_require_field(model_source, "suggested_files"), "suggested_files"):
        suggested_file = SuggestedTextFile.from_json(item)
        repaired_file, warning = _repair_markdown_code_fence(suggested_file, input_source)
        suggested_files.append(repaired_file.to_json())
        if warning is not None and warning not in warnings:
            warnings.append(warning)
    return {**model_source, "suggested_files": suggested_files, "warnings": warnings}


def _repair_markdown_code_fence(
    suggested_file: SuggestedTextFile,
    source: TextifySource,
) -> tuple[SuggestedTextFile, str | None]:
    if suggested_file.output_format != "markdown":
        return suggested_file, None
    if source.context.get("artifact_kind") in {"code", "log", "terminal"}:
        return suggested_file, None
    repaired_text = _unwrap_single_outer_markdown_code_fence(suggested_file.text)
    if repaired_text is None:
        return suggested_file, None
    if not repaired_text.strip():
        raise TextifyResponseError("markdown code fence repair produced empty text")
    return (
        SuggestedTextFile(
            suggested_path=suggested_file.suggested_path,
            output_format=suggested_file.output_format,
            text=repaired_text,
        ),
        MARKDOWN_CODE_FENCE_REPAIR_WARNING,
    )


def _unwrap_single_outer_markdown_code_fence(text: str) -> str | None:
    stripped = text.strip()
    lines = stripped.splitlines()
    if len(lines) < 2:
        return None
    opener = lines[0].strip()
    fence_length = len(opener) - len(opener.lstrip("`"))
    if fence_length < 3:
        return None
    info_string = opener[fence_length:]
    if "`" in info_string:
        return None
    fence = "`" * fence_length
    if lines[-1].strip() != fence:
        return None
    return "\n".join(lines[1:-1]).strip("\n")


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise TextifyResponseError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise TextifyResponseError(f"{field_name} must be a list")
    return cast(list[object], value)


def _require_field(payload: Mapping[str, JsonValue], field_name: str) -> JsonValue:
    if field_name not in payload:
        raise TextifyResponseError(f"{field_name} is required")
    return payload[field_name]


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TextifyResponseError(f"{field_name} must be a string")
    if not value.strip():
        raise TextifyResponseError(f"{field_name} must not be empty")
    return value


def _optional_non_negative_number(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool) or value < 0:
        raise TextifyResponseError(f"{field_name} must be a non-negative number")
    return value
