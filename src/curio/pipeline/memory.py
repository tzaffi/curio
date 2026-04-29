import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Final

from curio.pipeline.models import (
    ArtifactRef,
    JsonObject,
    JsonValue,
    ProcessCandidate,
    ProcessorObject,
    ProcessRecord,
    ProcessRef,
)

FAILED_STATUS: Final = "failed"


def _candidate_matches_record(candidate: ProcessCandidate, record: ProcessRecord) -> bool:
    return candidate.source_ref == record.source_ref and candidate.imsgx == record.imsgx


class InMemoryPipelineStore:
    def __init__(self, candidates_by_stage: Mapping[str, Sequence[ProcessCandidate]] | None = None) -> None:
        self._candidates_by_stage: dict[str, list[ProcessCandidate]] = {
            stage: list(candidates) for stage, candidates in (candidates_by_stage or {}).items()
        }
        self._records: list[ProcessRecord] = []

    @property
    def records(self) -> tuple[ProcessRecord, ...]:
        return tuple(self._records)

    def add_candidate(self, stage: str, candidate: ProcessCandidate) -> None:
        self._candidates_by_stage.setdefault(stage, []).append(candidate)

    def next_candidate(self, stage: str) -> ProcessCandidate | None:
        candidates = self._candidates_by_stage.get(stage, [])
        for candidate in candidates:
            if not self._has_record_for_candidate(stage, candidate):
                return candidate
        return None

    def existing_record(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ProcessRecord | None:
        for record in reversed(self._records):
            if (
                record.stage == stage
                and record.ledger_tab == ledger_tab
                and record.version == version
                and record.status != FAILED_STATUS
                and _candidate_matches_record(candidate, record)
            ):
                return record
        return None

    def append_record(self, record: ProcessRecord) -> ProcessRecord:
        self._records.append(record)
        return record

    def resolve_ref(self, ref: ProcessRef) -> ProcessRef:
        return ref

    def _has_record_for_candidate(self, stage: str, candidate: ProcessCandidate) -> bool:
        return any(record.stage == stage and _candidate_matches_record(candidate, record) for record in self._records)


class InMemoryArtifactStore:
    def __init__(self) -> None:
        self._objects: dict[str, JsonObject] = {}
        self._counter = 0

    @property
    def objects(self) -> Mapping[str, JsonObject]:
        return dict(self._objects)

    def persist_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
        object_: ProcessorObject,
    ) -> ArtifactRef:
        envelope: JsonObject = {
            "stage": stage,
            "ledger_tab": ledger_tab,
            "version": version,
            "source_ref": candidate.source_ref.to_json(),
            "iMsgX": candidate.imsgx.to_json(),
            "source": candidate.source,
            "artifact_key": candidate.artifact_key,
            "metadata": dict(candidate.metadata),
            "object": dict(object_.payload),
        }
        content = _json_bytes(envelope)
        digest = hashlib.sha256(content).hexdigest()
        self._counter += 1
        path = f"memory://{ledger_tab}/{self._counter:06d}-{digest[:12]}.json"
        self._objects[path] = envelope
        return ArtifactRef(
            kind=f"{stage}_object",
            mime_type=object_.mime_type,
            path=path,
            sha256=digest,
            size_bytes=len(content),
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
        )


def _json_bytes(value: Mapping[str, JsonValue]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
