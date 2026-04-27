from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, cast

from curio.llm_caller import LlmCostEstimate, LlmUsage, ProviderName
from curio.schemas import SchemaName, validate_json

JsonObject = dict[str, Any]
JsonValue = Any

TEXTIFY_REQUEST_VERSION = "curio-textify-request.v1"
TEXTIFY_RESPONSE_VERSION = "curio-textify-response.v1"
DEFAULT_TEXTIFY_OUTPUT_FORMAT = "auto"


class PreferredOutputFormat(StrEnum):
    AUTO = "auto"
    MARKDOWN = "markdown"
    TXT = "txt"


class TextifyStatus(StrEnum):
    CONVERTED = "converted"
    SKIPPED_TEXT_MEDIA = "skipped_text_media"
    UNSUPPORTED_MEDIA = "unsupported_media"
    NO_TEXT_FOUND = "no_text_found"


class TextifyError(Exception):
    pass


class TextifyRequestError(TextifyError):
    pass


class TextifyResponseError(TextifyError):
    pass


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_optional_non_negative_number(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative number")
    return value


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return cast(list[object], value)


def _require_field(payload: Mapping[str, JsonValue], field_name: str) -> JsonValue:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    return payload[field_name]


def _coerce_warnings(values: Sequence[str]) -> tuple[str, ...]:
    warnings = tuple(values)
    for warning in warnings:
        _require_string(warning, "warning")
    if len(warnings) != len(set(warnings)):
        raise ValueError("warnings must be unique")
    return warnings


def _coerce_string_sequence(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    items = tuple(values)
    for item in items:
        _require_string(item, field_name)
    if len(items) != len(set(items)):
        raise ValueError(f"{field_name} values must be unique")
    return items


def validate_suggested_path(value: str) -> str:
    path = _require_string(value, "suggested_path")
    if path.startswith(("~", "/", "\\")):
        raise TextifyResponseError("suggested_path must be a safe relative path")
    if "\\" in path:
        raise TextifyResponseError("suggested_path must use forward slashes")
    normalized = PurePosixPath(path)
    parts = normalized.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise TextifyResponseError("suggested_path must be normalized and relative")
    if ":" in parts[0]:
        raise TextifyResponseError("suggested_path must not contain a drive root")
    return normalized.as_posix()


@dataclass(frozen=True, slots=True)
class Artifact:
    artifact_id: int
    name: str
    path: str
    mime_type: str | None = None
    sha256: str | None = None
    source_language_hint: str | None = None
    context: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_positive_int(self.artifact_id, "artifact_id")
        _require_string(self.name, "name")
        _require_string(self.path, "path")
        if not Path(self.path).is_absolute():
            raise TextifyRequestError("artifact path must be absolute")
        if self.mime_type is not None:
            _require_string(self.mime_type, "mime_type")
        if self.sha256 is not None:
            _require_string(self.sha256, "sha256")
        if self.source_language_hint is not None:
            _require_string(self.source_language_hint, "source_language_hint")
        object.__setattr__(self, "context", dict(_require_mapping(self.context, "context")))

    @classmethod
    def from_json(cls, value: object) -> "Artifact":
        payload = _require_mapping(value, "artifact")
        mime_type = _require_field(payload, "mime_type")
        sha256 = _require_field(payload, "sha256")
        source_language_hint = _require_field(payload, "source_language_hint")
        return cls(
            artifact_id=_require_positive_int(_require_field(payload, "artifact_id"), "artifact_id"),
            name=_require_string(_require_field(payload, "name"), "name"),
            path=_require_string(_require_field(payload, "path"), "path"),
            mime_type=None if mime_type is None else _require_string(mime_type, "mime_type"),
            sha256=None if sha256 is None else _require_string(sha256, "sha256"),
            source_language_hint=None
            if source_language_hint is None
            else _require_string(source_language_hint, "source_language_hint"),
            context=_require_mapping(_require_field(payload, "context"), "context"),
        )

    def to_json(self) -> JsonObject:
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "path": self.path,
            "mime_type": self.mime_type,
            "sha256": self.sha256,
            "source_language_hint": self.source_language_hint,
            "context": dict(self.context),
        }


@dataclass(frozen=True, slots=True)
class TextifyRequest:
    request_id: str
    artifacts: Sequence[Artifact]
    preferred_output_format: PreferredOutputFormat | str = PreferredOutputFormat.AUTO
    llm_caller: str | None = None
    textify_request_version: str = field(default=TEXTIFY_REQUEST_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        object.__setattr__(self, "preferred_output_format", PreferredOutputFormat(self.preferred_output_format))
        artifacts = tuple(self.artifacts)
        if not artifacts:
            raise TextifyRequestError("artifacts must not be empty")
        artifact_ids = tuple(artifact.artifact_id for artifact in artifacts)
        if len(artifact_ids) != len(set(artifact_ids)):
            raise TextifyRequestError("artifact_id values must be unique")
        if self.llm_caller is not None:
            _require_string(self.llm_caller, "llm_caller")
        object.__setattr__(self, "artifacts", artifacts)

    @classmethod
    def from_json(cls, value: object) -> "TextifyRequest":
        validate_json(value, SchemaName.TEXTIFY_REQUEST)
        payload = _require_mapping(value, "textify request")
        llm_caller = _require_field(payload, "llm_caller")
        return cls(
            request_id=_require_string(_require_field(payload, "request_id"), "request_id"),
            preferred_output_format=_require_string(
                _require_field(payload, "preferred_output_format"),
                "preferred_output_format",
            ),
            artifacts=[
                Artifact.from_json(artifact)
                for artifact in _require_list(_require_field(payload, "artifacts"), "artifacts")
            ],
            llm_caller=None if llm_caller is None else _require_string(llm_caller, "llm_caller"),
        )

    def to_json(self) -> JsonObject:
        preferred_output_format = cast(PreferredOutputFormat, self.preferred_output_format)
        return {
            "textify_request_version": self.textify_request_version,
            "request_id": self.request_id,
            "preferred_output_format": preferred_output_format.value,
            "artifacts": [artifact.to_json() for artifact in self.artifacts],
            "llm_caller": self.llm_caller,
        }


@dataclass(frozen=True, slots=True)
class SuggestedTextFile:
    suggested_path: str
    output_format: str
    text: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "suggested_path", validate_suggested_path(self.suggested_path))
        _require_string(self.output_format, "output_format")
        if self.output_format == PreferredOutputFormat.AUTO.value:
            raise TextifyResponseError("output_format must not be auto")
        _require_string(self.text, "text")

    @classmethod
    def from_json(cls, value: object) -> "SuggestedTextFile":
        payload = _require_mapping(value, "suggested file")
        return cls(
            suggested_path=_require_string(_require_field(payload, "suggested_path"), "suggested_path"),
            output_format=_require_string(_require_field(payload, "output_format"), "output_format"),
            text=_require_string(_require_field(payload, "text"), "text"),
        )

    def to_json(self) -> JsonObject:
        return {
            "suggested_path": self.suggested_path,
            "output_format": self.output_format,
            "text": self.text,
        }


@dataclass(frozen=True, slots=True)
class TextifiedArtifact:
    artifact_id: int
    name: str
    input_mime_type: str | None
    source_sha256: str | None
    textification_required: bool
    status: TextifyStatus | str
    suggested_files: Sequence[SuggestedTextFile] = field(default_factory=tuple)
    detected_languages: Sequence[str] = field(default_factory=tuple)
    page_count: float | int | None = None
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_positive_int(self.artifact_id, "artifact_id")
        _require_string(self.name, "name")
        if self.input_mime_type is not None:
            _require_string(self.input_mime_type, "input_mime_type")
        if self.source_sha256 is not None:
            _require_string(self.source_sha256, "source_sha256")
        _require_bool(self.textification_required, "textification_required")
        object.__setattr__(self, "status", TextifyStatus(self.status))
        suggested_files = tuple(self.suggested_files)
        status = cast(TextifyStatus, self.status)
        if status == TextifyStatus.CONVERTED and not suggested_files:
            raise TextifyResponseError("converted artifacts must include suggested_files")
        if status != TextifyStatus.CONVERTED and suggested_files:
            raise TextifyResponseError("non-converted artifacts must not include suggested_files")
        object.__setattr__(self, "suggested_files", suggested_files)
        object.__setattr__(self, "detected_languages", _coerce_string_sequence(self.detected_languages, "language"))
        _require_optional_non_negative_number(self.page_count, "page_count")
        object.__setattr__(self, "warnings", _coerce_warnings(self.warnings))

    @classmethod
    def from_json(cls, value: object) -> "TextifiedArtifact":
        payload = _require_mapping(value, "textified artifact")
        input_mime_type = _require_field(payload, "input_mime_type")
        source_sha256 = _require_field(payload, "source_sha256")
        return cls(
            artifact_id=_require_positive_int(_require_field(payload, "artifact_id"), "artifact_id"),
            name=_require_string(_require_field(payload, "name"), "name"),
            input_mime_type=None
            if input_mime_type is None
            else _require_string(input_mime_type, "input_mime_type"),
            source_sha256=None if source_sha256 is None else _require_string(source_sha256, "source_sha256"),
            textification_required=_require_bool(
                _require_field(payload, "textification_required"),
                "textification_required",
            ),
            status=_require_string(_require_field(payload, "status"), "status"),
            suggested_files=[
                SuggestedTextFile.from_json(item)
                for item in _require_list(_require_field(payload, "suggested_files"), "suggested_files")
            ],
            detected_languages=[
                _require_string(language, "language")
                for language in _require_list(_require_field(payload, "detected_languages"), "detected_languages")
            ],
            page_count=_require_optional_non_negative_number(_require_field(payload, "page_count"), "page_count"),
            warnings=[
                _require_string(warning, "warning")
                for warning in _require_list(_require_field(payload, "warnings"), "warnings")
            ],
        )

    def to_json(self) -> JsonObject:
        status = cast(TextifyStatus, self.status)
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "input_mime_type": self.input_mime_type,
            "source_sha256": self.source_sha256,
            "textification_required": self.textification_required,
            "status": status.value,
            "suggested_files": [suggested_file.to_json() for suggested_file in self.suggested_files],
            "detected_languages": list(self.detected_languages),
            "page_count": self.page_count,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class TextifyLlmSummary:
    provider: ProviderName | str
    model: str | None
    usage: LlmUsage
    cost_estimate: LlmCostEstimate | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", ProviderName(self.provider))
        if self.model is not None:
            _require_string(self.model, "model")

    @classmethod
    def from_json(cls, value: object) -> "TextifyLlmSummary":
        payload = _require_mapping(value, "llm")
        cost_estimate = _require_field(payload, "cost_estimate")
        return cls(
            provider=_require_string(_require_field(payload, "provider"), "provider"),
            model=cast(str | None, _require_field(payload, "model")),
            usage=LlmUsage.from_json(_require_field(payload, "usage")),
            cost_estimate=None if cost_estimate is None else LlmCostEstimate.from_json(cost_estimate),
        )

    def to_json(self) -> JsonObject:
        provider = cast(ProviderName, self.provider)
        return {
            "provider": provider.value,
            "model": self.model,
            "usage": self.usage.to_json(),
            "cost_estimate": None if self.cost_estimate is None else self.cost_estimate.to_json(),
        }


@dataclass(frozen=True, slots=True)
class TextifyResponse:
    request_id: str
    artifacts: Sequence[TextifiedArtifact]
    llm: TextifyLlmSummary | None = None
    warnings: Sequence[str] = field(default_factory=tuple)
    textify_response_version: str = field(default=TEXTIFY_RESPONSE_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        artifacts = tuple(self.artifacts)
        if not artifacts:
            raise TextifyResponseError("artifacts must not be empty")
        artifact_ids = tuple(artifact.artifact_id for artifact in artifacts)
        if len(artifact_ids) != len(set(artifact_ids)):
            raise TextifyResponseError("artifact_id values must be unique")
        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(self, "warnings", _coerce_warnings(self.warnings))

    @classmethod
    def from_json(cls, value: object) -> "TextifyResponse":
        validate_json(value, SchemaName.TEXTIFY_RESPONSE)
        payload = _require_mapping(value, "textify response")
        llm = _require_field(payload, "llm")
        return cls(
            request_id=_require_string(_require_field(payload, "request_id"), "request_id"),
            artifacts=[
                TextifiedArtifact.from_json(artifact)
                for artifact in _require_list(_require_field(payload, "artifacts"), "artifacts")
            ],
            llm=None if llm is None else TextifyLlmSummary.from_json(llm),
            warnings=[
                _require_string(warning, "warning")
                for warning in _require_list(_require_field(payload, "warnings"), "warnings")
            ],
        )

    def to_json(self) -> JsonObject:
        return {
            "textify_response_version": self.textify_response_version,
            "request_id": self.request_id,
            "artifacts": [artifact.to_json() for artifact in self.artifacts],
            "llm": None if self.llm is None else self.llm.to_json(),
            "warnings": list(self.warnings),
        }
