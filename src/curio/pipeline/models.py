from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, Self, cast

JsonObject = dict[str, Any]
JsonValue = Any


class PipelineStage(StrEnum):
    TEXTIFY = "textify"
    TRANSLATE = "translate"


class LedgerTab(StrEnum):
    TEXTIFICATIONS = "textifications"
    TRANSLATIONS = "translations"


class TextifyProcessStatus(StrEnum):
    CONVERTED = "converted"
    ALREADY_TEXT = "already_text"
    UNSUPPORTED = "unsupported"
    NO_TEXT = "no_text"
    FAILED = "failed"


class TranslateProcessStatus(StrEnum):
    TRANSLATED = "translated"
    ALREADY_ENGLISH = "already_english"
    FAILED = "failed"


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_optional_string(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, field_name)


def _require_optional_positive_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_optional_non_negative_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _optional_field(payload: Mapping[str, JsonValue], field_name: str) -> JsonValue:
    return payload[field_name] if field_name in payload else None


def _require_field(payload: Mapping[str, JsonValue], field_name: str) -> JsonValue:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    return payload[field_name]


@dataclass(frozen=True, slots=True)
class ProcessRef:
    stage: str
    tab: str
    source: str
    row_number: int | None = None
    row_url: str | None = None
    spreadsheet_id: str | None = None
    sheet_id: str | None = None
    artifact_url: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None

    def __post_init__(self) -> None:
        _require_string(self.stage, "stage")
        _require_string(self.tab, "tab")
        _require_string(self.source, "source")
        _require_optional_positive_int(self.row_number, "row_number")
        _require_optional_string(self.row_url, "row_url")
        _require_optional_string(self.spreadsheet_id, "spreadsheet_id")
        _require_optional_string(self.sheet_id, "sheet_id")
        _require_optional_string(self.artifact_url, "artifact_url")
        _require_optional_string(self.artifact_path, "artifact_path")
        _require_optional_string(self.artifact_sha256, "artifact_sha256")

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "process ref")
        return cls(
            stage=_require_string(_require_field(payload, "stage"), "stage"),
            tab=_require_string(_require_field(payload, "tab"), "tab"),
            source=_require_string(_require_field(payload, "source"), "source"),
            row_number=_require_optional_positive_int(_optional_field(payload, "row_number"), "row_number"),
            row_url=_require_optional_string(_optional_field(payload, "row_url"), "row_url"),
            spreadsheet_id=_require_optional_string(_optional_field(payload, "spreadsheet_id"), "spreadsheet_id"),
            sheet_id=_require_optional_string(_optional_field(payload, "sheet_id"), "sheet_id"),
            artifact_url=_require_optional_string(_optional_field(payload, "artifact_url"), "artifact_url"),
            artifact_path=_require_optional_string(_optional_field(payload, "artifact_path"), "artifact_path"),
            artifact_sha256=_require_optional_string(_optional_field(payload, "artifact_sha256"), "artifact_sha256"),
        )

    def to_json(self) -> JsonObject:
        return {
            "stage": self.stage,
            "tab": self.tab,
            "source": self.source,
            "row_number": self.row_number,
            "row_url": self.row_url,
            "spreadsheet_id": self.spreadsheet_id,
            "sheet_id": self.sheet_id,
            "artifact_url": self.artifact_url,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
        }


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    kind: str
    mime_type: str
    url: str | None = None
    path: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    source_ref: ProcessRef | None = None
    imsgx: ProcessRef | None = None

    def __post_init__(self) -> None:
        _require_string(self.kind, "kind")
        _require_string(self.mime_type, "mime_type")
        _require_optional_string(self.url, "url")
        _require_optional_string(self.path, "path")
        _require_optional_string(self.sha256, "sha256")
        _require_optional_non_negative_int(self.size_bytes, "size_bytes")
        if self.url is None and self.path is None:
            raise ValueError("artifact ref requires url or path")
        if self.source_ref is not None and not isinstance(self.source_ref, ProcessRef):
            raise ValueError("source_ref must be a ProcessRef")
        if self.imsgx is not None and not isinstance(self.imsgx, ProcessRef):
            raise ValueError("imsgx must be a ProcessRef")

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "artifact ref")
        source_ref = _optional_field(payload, "source_ref")
        imsgx = _optional_field(payload, "iMsgX")
        return cls(
            kind=_require_string(_require_field(payload, "kind"), "kind"),
            mime_type=_require_string(_require_field(payload, "mime_type"), "mime_type"),
            url=_require_optional_string(_optional_field(payload, "url"), "url"),
            path=_require_optional_string(_optional_field(payload, "path"), "path"),
            sha256=_require_optional_string(_optional_field(payload, "sha256"), "sha256"),
            size_bytes=_require_optional_non_negative_int(_optional_field(payload, "size_bytes"), "size_bytes"),
            source_ref=None if source_ref is None else ProcessRef.from_json(source_ref),
            imsgx=None if imsgx is None else ProcessRef.from_json(imsgx),
        )

    def to_json(self) -> JsonObject:
        return {
            "kind": self.kind,
            "mime_type": self.mime_type,
            "url": self.url,
            "path": self.path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "source_ref": None if self.source_ref is None else self.source_ref.to_json(),
            "iMsgX": None if self.imsgx is None else self.imsgx.to_json(),
        }


@dataclass(frozen=True, slots=True)
class ProcessCandidate:
    source_ref: ProcessRef
    imsgx: ProcessRef
    source: str
    artifact_key: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, ProcessRef):
            raise ValueError("source_ref must be a ProcessRef")
        if not isinstance(self.imsgx, ProcessRef):
            raise ValueError("imsgx must be a ProcessRef")
        _require_string(self.source, "source")
        _require_optional_string(self.artifact_key, "artifact_key")
        object.__setattr__(self, "metadata", dict(_require_mapping(self.metadata, "metadata")))

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "process candidate")
        return cls(
            source_ref=ProcessRef.from_json(_require_field(payload, "source_ref")),
            imsgx=ProcessRef.from_json(_require_field(payload, "iMsgX")),
            source=_require_string(_require_field(payload, "source"), "source"),
            artifact_key=_require_optional_string(_optional_field(payload, "artifact_key"), "artifact_key"),
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        return {
            "source_ref": self.source_ref.to_json(),
            "iMsgX": self.imsgx.to_json(),
            "source": self.source,
            "artifact_key": self.artifact_key,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class Eligibility:
    eligible: bool
    status: str
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_bool(self.eligible, "eligible")
        _require_string(self.status, "status")
        object.__setattr__(self, "metadata", dict(_require_mapping(self.metadata, "metadata")))

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "eligibility")
        return cls(
            eligible=_require_bool(_require_field(payload, "eligible"), "eligible"),
            status=_require_string(_require_field(payload, "status"), "status"),
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        return {
            "eligible": self.eligible,
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProcessorObject:
    payload: Mapping[str, JsonValue]
    mime_type: str = "application/json"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(_require_mapping(self.payload, "payload")))
        _require_string(self.mime_type, "mime_type")

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "processor object")
        return cls(
            payload=_require_mapping(_require_field(payload, "payload"), "payload"),
            mime_type=_require_string(_require_field(payload, "mime_type"), "mime_type"),
        )

    def to_json(self) -> JsonObject:
        return {
            "payload": dict(self.payload),
            "mime_type": self.mime_type,
        }


@dataclass(frozen=True, slots=True)
class ProcessOutcome:
    status: str
    object_: ProcessorObject | None = None
    output_source: ProcessRef | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_string(self.status, "status")
        if self.object_ is not None and not isinstance(self.object_, ProcessorObject):
            raise ValueError("object_ must be a ProcessorObject")
        if self.output_source is not None and not isinstance(self.output_source, ProcessRef):
            raise ValueError("output_source must be a ProcessRef")
        object.__setattr__(self, "metadata", dict(_require_mapping(self.metadata, "metadata")))

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "process outcome")
        object_payload = _optional_field(payload, "object")
        output_source = _optional_field(payload, "output_source")
        return cls(
            status=_require_string(_require_field(payload, "status"), "status"),
            object_=None if object_payload is None else ProcessorObject.from_json(object_payload),
            output_source=None if output_source is None else ProcessRef.from_json(output_source),
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        return {
            "status": self.status,
            "object": None if self.object_ is None else self.object_.to_json(),
            "output_source": None if self.output_source is None else self.output_source.to_json(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PersistedOutcome:
    status: str
    object_: ArtifactRef | None = None
    output_source: ProcessRef | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_string(self.status, "status")
        if self.object_ is not None and not isinstance(self.object_, ArtifactRef):
            raise ValueError("object_ must be an ArtifactRef")
        if self.output_source is not None and not isinstance(self.output_source, ProcessRef):
            raise ValueError("output_source must be a ProcessRef")
        object.__setattr__(self, "metadata", dict(_require_mapping(self.metadata, "metadata")))

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "persisted outcome")
        object_payload = _optional_field(payload, "object")
        output_source = _optional_field(payload, "output_source")
        return cls(
            status=_require_string(_require_field(payload, "status"), "status"),
            object_=None if object_payload is None else ArtifactRef.from_json(object_payload),
            output_source=None if output_source is None else ProcessRef.from_json(output_source),
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        return {
            "status": self.status,
            "object": None if self.object_ is None else self.object_.to_json(),
            "output_source": None if self.output_source is None else self.output_source.to_json(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProcessRecord:
    stage: str
    ledger_tab: str
    version: str
    source_ref: ProcessRef
    imsgx: ProcessRef
    status: str
    object_: ArtifactRef | None = None
    output_source: ProcessRef | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_string(self.stage, "stage")
        _require_string(self.ledger_tab, "ledger_tab")
        _require_string(self.version, "version")
        if not isinstance(self.source_ref, ProcessRef):
            raise ValueError("source_ref must be a ProcessRef")
        if not isinstance(self.imsgx, ProcessRef):
            raise ValueError("imsgx must be a ProcessRef")
        _require_string(self.status, "status")
        if self.object_ is not None and not isinstance(self.object_, ArtifactRef):
            raise ValueError("object_ must be an ArtifactRef")
        if self.output_source is not None and not isinstance(self.output_source, ProcessRef):
            raise ValueError("output_source must be a ProcessRef")
        object.__setattr__(self, "metadata", dict(_require_mapping(self.metadata, "metadata")))

    @classmethod
    def from_json(cls, value: object) -> Self:
        payload = _require_mapping(value, "process record")
        object_payload = _optional_field(payload, "object")
        output_source = _optional_field(payload, "output_source")
        return cls(
            stage=_require_string(_require_field(payload, "stage"), "stage"),
            ledger_tab=_require_string(_require_field(payload, "ledger_tab"), "ledger_tab"),
            version=_require_string(_require_field(payload, "version"), "version"),
            source_ref=ProcessRef.from_json(_require_field(payload, "source_ref")),
            imsgx=ProcessRef.from_json(_require_field(payload, "iMsgX")),
            status=_require_string(_require_field(payload, "status"), "status"),
            object_=None if object_payload is None else ArtifactRef.from_json(object_payload),
            output_source=None if output_source is None else ProcessRef.from_json(output_source),
            metadata=_require_mapping(_require_field(payload, "metadata"), "metadata"),
        )

    def to_json(self) -> JsonObject:
        return {
            "stage": self.stage,
            "ledger_tab": self.ledger_tab,
            "version": self.version,
            "source_ref": self.source_ref.to_json(),
            "iMsgX": self.imsgx.to_json(),
            "status": self.status,
            "object": None if self.object_ is None else self.object_.to_json(),
            "output_source": None if self.output_source is None else self.output_source.to_json(),
            "metadata": dict(self.metadata),
        }


class PipelineStore(Protocol):
    def next_candidate(self, stage: str) -> ProcessCandidate | None: ...

    def existing_record(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ProcessRecord | None: ...

    def append_record(self, record: ProcessRecord) -> ProcessRecord: ...

    def resolve_ref(self, ref: ProcessRef) -> ProcessRef: ...


class ArtifactStore(Protocol):
    def persist_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
        object_: ProcessorObject,
    ) -> ArtifactRef: ...


class Processor(ABC):
    stage: str
    ledger_tab: str
    version: str

    def validate_identity(self) -> None:
        _require_string(self.stage, "stage")
        _require_string(self.ledger_tab, "ledger_tab")
        _require_string(self.version, "version")

    @abstractmethod
    def next_candidate(self, store: PipelineStore) -> ProcessCandidate | None:
        raise NotImplementedError

    @abstractmethod
    def eligibility(self, candidate: ProcessCandidate) -> Eligibility:
        raise NotImplementedError

    @abstractmethod
    def process(self, candidate: ProcessCandidate) -> ProcessOutcome:
        raise NotImplementedError

    @abstractmethod
    def persist(
        self,
        candidate: ProcessCandidate,
        outcome: ProcessOutcome,
        artifacts: ArtifactStore,
    ) -> PersistedOutcome:
        raise NotImplementedError

    @abstractmethod
    def record(
        self,
        candidate: ProcessCandidate,
        outcome: PersistedOutcome,
        store: PipelineStore,
    ) -> ProcessRecord:
        raise NotImplementedError
