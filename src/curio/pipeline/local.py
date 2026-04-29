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

    @classmethod
    def from_config(cls, config: PipelineConfig) -> Self:
        return cls(config.effective_artifact_root)

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
        directory = self.root / ledger_tab
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / _artifact_filename(stage, candidate)
        _write_new_or_matching_content(path, content)
        return ArtifactRef(
            kind=f"{stage}_object",
            mime_type=object_.mime_type,
            path=str(path),
            sha256=digest,
            size_bytes=len(content),
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
        )


def _artifact_filename(stage: str, candidate: ProcessCandidate) -> str:
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


def _write_new_or_matching_content(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError(f"local artifact already exists with different content: {path}")
        return
    path.write_bytes(content)
