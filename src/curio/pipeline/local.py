import hashlib
import re
from pathlib import Path
from typing import Self

from curio.config import PipelineConfig
from curio.pipeline.memory import _json_bytes
from curio.pipeline.models import (
    ArtifactRef,
    JsonObject,
    ProcessCandidate,
    ProcessorObject,
)

IMSGX_STEM_RE = re.compile(r"^(imsgx-r\d{4})-(.+)$")
SLUG_RE = re.compile(r"[^a-z0-9]+")


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._created_paths: set[Path] = set()

    @classmethod
    def from_config(cls, config: PipelineConfig) -> Self:
        return cls(config.effective_artifact_root)

    def existing_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ArtifactRef | None:
        del version
        path = self.root / ledger_tab / artifact_filename(stage, candidate)
        if not path.exists():
            return None
        content = path.read_bytes()
        return ArtifactRef(
            kind=f"{stage}_object",
            mime_type="application/json",
            path=str(path),
            sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
        )

    def persist_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
        object_: ProcessorObject,
    ) -> ArtifactRef:
        envelope = artifact_envelope(stage=stage, ledger_tab=ledger_tab, version=version, candidate=candidate, object_=object_)
        content = _json_bytes(envelope)
        directory = self.root / ledger_tab
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / artifact_filename(stage, candidate)
        persisted_content, created = _write_new_or_existing_content(path, content)
        if created:
            self._created_paths.add(path)
        digest = hashlib.sha256(persisted_content).hexdigest()
        return ArtifactRef(
            kind=f"{stage}_object",
            mime_type=object_.mime_type,
            path=str(path),
            sha256=digest,
            size_bytes=len(persisted_content),
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
        )

    def discard_object(self, ref: ArtifactRef) -> None:
        if ref.path is None:
            return
        path = Path(ref.path)
        if path not in self._created_paths:
            return
        path.unlink(missing_ok=True)
        self._created_paths.remove(path)


def artifact_envelope(
    *,
    stage: str,
    ledger_tab: str,
    version: str,
    candidate: ProcessCandidate,
    object_: ProcessorObject,
) -> JsonObject:
    return {
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


def artifact_filename(stage: str, candidate: ProcessCandidate) -> str:
    stem = _source_artifact_stem(candidate)
    if stem is not None:
        match = IMSGX_STEM_RE.match(stem)
        if match is not None:
            return f"{match.group(1)}-{stage}-{match.group(2)}.json"
    if candidate.source_ref.row_number is not None:
        return f"imsgx-r{candidate.source_ref.row_number:04d}-{stage}-{_slugify(candidate.source)}.json"
    digest = hashlib.sha256(_json_bytes(candidate.to_json())).hexdigest()[:12]
    return f"imsgx-{stage}-{digest}.json"


def _source_artifact_stem(candidate: ProcessCandidate) -> str | None:
    for value in (candidate.source_ref.artifact_path, candidate.artifact_key):
        if value is not None:
            stem = Path(value).stem
            if stem:
                return stem
    return None


def _slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.casefold()).strip("-")
    return slug[:80].strip("-") if slug else "source"


def _write_new_or_existing_content(path: Path, content: bytes) -> tuple[bytes, bool]:
    if path.exists():
        return path.read_bytes(), False
    path.write_bytes(content)
    return content, True
