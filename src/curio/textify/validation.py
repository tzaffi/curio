from collections.abc import Mapping, Sequence
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError

from curio.llm_caller import LlmResponse, LlmStatus
from curio.textify.adapter import textify_model_output_schema
from curio.textify.media import effective_mime_type, source_sha256
from curio.textify.models import (
    Artifact,
    JsonValue,
    SuggestedTextFile,
    TextifiedArtifact,
    TextifyRequest,
    TextifyResponseError,
    TextifyStatus,
)


def textified_artifacts_from_llm_response(
    request: TextifyRequest,
    artifact: Artifact,
    response: LlmResponse,
) -> tuple[TextifiedArtifact, ...]:
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

    model_artifacts = tuple(
        _model_artifact_from_json(item)
        for item in _require_list(_require_field(payload, "artifacts"), "artifacts")
    )
    validate_textified_model_artifacts((artifact,), model_artifacts)
    return tuple(_response_artifact_from_model(artifact, model_artifact) for model_artifact in model_artifacts)


def validate_textify_model_output(value: JsonValue) -> None:
    validator = Draft202012Validator(textify_model_output_schema(), format_checker=FormatChecker())
    try:
        validator.validate(value)
    except JsonSchemaLibraryError as exc:
        raise TextifyResponseError(f"LLM output failed textify schema validation: {exc.message}") from exc


def validate_textified_model_artifacts(
    input_artifacts: Sequence[Artifact],
    model_artifacts: Sequence[Mapping[str, JsonValue]],
) -> None:
    model_artifacts = tuple(_model_artifact_from_json(model_artifact) for model_artifact in model_artifacts)
    input_ids = tuple(artifact.artifact_id for artifact in input_artifacts)
    output_ids = tuple(_model_artifact_id(model_artifact) for model_artifact in model_artifacts)
    duplicated_ids = _duplicated_ids(output_ids)
    if duplicated_ids:
        raise TextifyResponseError(f"duplicate textified artifact ids: {_format_ids(duplicated_ids)}")
    missing_ids = tuple(artifact_id for artifact_id in input_ids if artifact_id not in output_ids)
    if missing_ids:
        raise TextifyResponseError(f"missing textified artifact ids: {_format_ids(missing_ids)}")
    extra_ids = tuple(artifact_id for artifact_id in output_ids if artifact_id not in input_ids)
    if extra_ids:
        raise TextifyResponseError(f"unexpected textified artifact ids: {_format_ids(extra_ids)}")
    if output_ids != input_ids:
        raise TextifyResponseError("textified artifact order must match input artifact order")
    input_by_id = {artifact.artifact_id: artifact for artifact in input_artifacts}
    for model_artifact in model_artifacts:
        artifact_id = _model_artifact_id(model_artifact)
        input_artifact = input_by_id[artifact_id]
        if _require_string(_require_field(model_artifact, "name"), "name") != input_artifact.name:
            raise TextifyResponseError(f"textified artifact name must match input artifact name for artifact_id {artifact_id}")
        status = TextifyStatus(_require_string(_require_field(model_artifact, "status"), "status"))
        suggested_files = [
            SuggestedTextFile.from_json(item)
            for item in _require_list(_require_field(model_artifact, "suggested_files"), "suggested_files")
        ]
        if status == TextifyStatus.CONVERTED and not suggested_files:
            raise TextifyResponseError("converted artifacts must include suggested_files")
        if status != TextifyStatus.CONVERTED and suggested_files:
            raise TextifyResponseError("non-converted artifacts must not include suggested_files")
        _require_list(_require_field(model_artifact, "warnings"), "warnings")
        _optional_non_negative_number(_require_field(model_artifact, "page_count"), "page_count")
        for suggested_file in suggested_files:
            _reject_useless_markdown_code_fence(suggested_file, input_artifact)


def _response_artifact_from_model(
    input_artifact: Artifact,
    model_artifact: Mapping[str, JsonValue],
) -> TextifiedArtifact:
    return TextifiedArtifact(
        artifact_id=input_artifact.artifact_id,
        name=input_artifact.name,
        input_mime_type=effective_mime_type(input_artifact),
        source_sha256=source_sha256(input_artifact),
        textification_required=True,
        status=TextifyStatus(_require_string(_require_field(model_artifact, "status"), "status")),
        suggested_files=[
            SuggestedTextFile.from_json(item)
            for item in _require_list(_require_field(model_artifact, "suggested_files"), "suggested_files")
        ],
        detected_languages=[
            _require_string(language, "language")
            for language in _require_list(_require_field(model_artifact, "detected_languages"), "detected_languages")
        ],
        page_count=_optional_non_negative_number(_require_field(model_artifact, "page_count"), "page_count"),
        warnings=[
            _require_string(warning, "warning")
            for warning in _require_list(_require_field(model_artifact, "warnings"), "warnings")
        ],
    )


def _model_artifact_from_json(value: object) -> Mapping[str, JsonValue]:
    return _require_mapping(value, "model artifact")


def _model_artifact_id(value: Mapping[str, JsonValue]) -> int:
    artifact_id = _require_field(value, "artifact_id")
    if not isinstance(artifact_id, int) or isinstance(artifact_id, bool) or artifact_id < 1:
        raise TextifyResponseError("artifact_id must be a positive integer")
    return artifact_id


def _reject_useless_markdown_code_fence(suggested_file: SuggestedTextFile, artifact: Artifact) -> None:
    if suggested_file.output_format != "markdown":
        return
    text = suggested_file.text.strip()
    if not text.startswith("```") or not text.endswith("```"):
        return
    if artifact.context.get("artifact_kind") in {"code", "log", "terminal"}:
        return
    raise TextifyResponseError("markdown output must not be wrapped in a single code fence")


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


def _duplicated_ids(ids: Sequence[int]) -> tuple[int, ...]:
    seen: set[int] = set()
    duplicates: list[int] = []
    for identifier in ids:
        if identifier in seen and identifier not in duplicates:
            duplicates.append(identifier)
        seen.add(identifier)
    return tuple(duplicates)


def _format_ids(ids: Sequence[int]) -> str:
    return ", ".join(str(identifier) for identifier in ids)
