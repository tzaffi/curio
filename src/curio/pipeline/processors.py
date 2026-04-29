import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from curio.pipeline.models import (
    ArtifactRef,
    ArtifactStore,
    Eligibility,
    JsonValue,
    LedgerTab,
    PersistedOutcome,
    PipelineStage,
    PipelineStore,
    ProcessCandidate,
    Processor,
    ProcessorObject,
    ProcessOutcome,
    ProcessRecord,
    ProcessRef,
    TextifyProcessStatus,
    TranslateProcessStatus,
)
from curio.textify import (
    DEFAULT_TEXTIFY_OUTPUT_FORMAT,
    TextifyRequest,
    TextifyResponse,
    TextifySource,
    TextifyStatus,
)
from curio.translate import (
    DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD,
    DEFAULT_TARGET_LANGUAGE,
    Block,
    TranslationRequest,
    TranslationResponse,
)

TEXTIFY_PROCESSOR_VERSION = "curio-textify-processor.v1"
TRANSLATE_PROCESSOR_VERSION = "curio-translate-processor.v1"


class TextifyServiceBoundary(Protocol):
    def textify(self, request: TextifyRequest) -> TextifyResponse: ...


class TranslationServiceBoundary(Protocol):
    def translate(self, request: TranslationRequest) -> TranslationResponse: ...


@dataclass(frozen=True, slots=True)
class TextifyProcessor(Processor):
    service: TextifyServiceBoundary
    version: str = TEXTIFY_PROCESSOR_VERSION
    stage: str = PipelineStage.TEXTIFY.value
    ledger_tab: str = LedgerTab.TEXTIFICATIONS.value

    def next_candidate(self, store: PipelineStore) -> ProcessCandidate | None:
        self.validate_identity()
        return store.next_candidate(self.stage)

    def eligibility(self, candidate: ProcessCandidate) -> Eligibility:
        return Eligibility(eligible=True, status=TextifyProcessStatus.CONVERTED.value)

    def process(self, candidate: ProcessCandidate) -> ProcessOutcome:
        request = _textify_request_from_candidate(candidate)
        response = self.service.textify(request)
        status = _textify_process_status(response)
        object_ = ProcessorObject(payload=response.to_json()) if status == TextifyProcessStatus.CONVERTED.value else None
        return ProcessOutcome(
            status=status,
            object_=object_,
            output_source=candidate.source_ref if status == TextifyProcessStatus.ALREADY_TEXT.value else None,
            metadata={
                "request_id": response.request_id,
                "textify_status": cast(TextifyStatus, response.source.status).value,
                "warnings": list(response.warnings) + list(response.source.warnings),
            },
        )

    def persist(
        self,
        candidate: ProcessCandidate,
        outcome: ProcessOutcome,
        artifacts: ArtifactStore,
    ) -> PersistedOutcome:
        if outcome.object_ is None:
            return PersistedOutcome(
                status=outcome.status,
                output_source=outcome.output_source,
                metadata=outcome.metadata,
            )
        artifact = artifacts.persist_object(
            stage=self.stage,
            ledger_tab=self.ledger_tab,
            version=self.version,
            candidate=candidate,
            object_=outcome.object_,
        )
        return PersistedOutcome(
            status=outcome.status,
            object_=artifact,
            output_source=_artifact_output_ref(self.stage, self.ledger_tab, candidate, artifact),
            metadata=outcome.metadata,
        )

    def record(
        self,
        candidate: ProcessCandidate,
        outcome: PersistedOutcome,
        store: PipelineStore,
    ) -> ProcessRecord:
        return store.append_record(
            ProcessRecord(
                stage=self.stage,
                ledger_tab=self.ledger_tab,
                version=self.version,
                source_ref=candidate.source_ref,
                imsgx=candidate.imsgx,
                status=outcome.status,
                object_=outcome.object_,
                output_source=outcome.output_source,
                metadata=outcome.metadata,
            )
        )


@dataclass(frozen=True, slots=True)
class TranslateProcessor(Processor):
    service: TranslationServiceBoundary
    version: str = TRANSLATE_PROCESSOR_VERSION
    stage: str = PipelineStage.TRANSLATE.value
    ledger_tab: str = LedgerTab.TRANSLATIONS.value

    def next_candidate(self, store: PipelineStore) -> ProcessCandidate | None:
        self.validate_identity()
        return store.next_candidate(self.stage)

    def eligibility(self, candidate: ProcessCandidate) -> Eligibility:
        return Eligibility(eligible=True, status=TranslateProcessStatus.TRANSLATED.value)

    def process(self, candidate: ProcessCandidate) -> ProcessOutcome:
        request = _translation_request_from_candidate(candidate)
        response = self.service.translate(request)
        status = _translate_process_status(response)
        object_ = ProcessorObject(payload=response.to_json()) if status == TranslateProcessStatus.TRANSLATED.value else None
        return ProcessOutcome(
            status=status,
            object_=object_,
            output_source=candidate.source_ref if status == TranslateProcessStatus.ALREADY_ENGLISH.value else None,
            metadata={
                "request_id": response.request_id,
                "translated_blocks": sum(block.translation_required for block in response.blocks),
                "warnings": list(response.warnings) + [warning for block in response.blocks for warning in block.warnings],
            },
        )

    def persist(
        self,
        candidate: ProcessCandidate,
        outcome: ProcessOutcome,
        artifacts: ArtifactStore,
    ) -> PersistedOutcome:
        if outcome.object_ is None:
            return PersistedOutcome(
                status=outcome.status,
                output_source=outcome.output_source,
                metadata=outcome.metadata,
            )
        artifact = artifacts.persist_object(
            stage=self.stage,
            ledger_tab=self.ledger_tab,
            version=self.version,
            candidate=candidate,
            object_=outcome.object_,
        )
        return PersistedOutcome(
            status=outcome.status,
            object_=artifact,
            output_source=_artifact_output_ref(self.stage, self.ledger_tab, candidate, artifact),
            metadata=outcome.metadata,
        )

    def record(
        self,
        candidate: ProcessCandidate,
        outcome: PersistedOutcome,
        store: PipelineStore,
    ) -> ProcessRecord:
        return store.append_record(
            ProcessRecord(
                stage=self.stage,
                ledger_tab=self.ledger_tab,
                version=self.version,
                source_ref=candidate.source_ref,
                imsgx=candidate.imsgx,
                status=outcome.status,
                object_=outcome.object_,
                output_source=outcome.output_source,
                metadata=outcome.metadata,
            )
        )


def _textify_request_from_candidate(candidate: ProcessCandidate) -> TextifyRequest:
    metadata = candidate.metadata
    path = _metadata_string(metadata, "path", candidate.source_ref.artifact_path)
    if path is None:
        raise ValueError("textify candidate metadata requires path or source_ref.artifact_path")
    context = dict(_metadata_mapping(metadata, "context", {}))
    evidence_text = _metadata_string(metadata, "evidence_text")
    if evidence_text is not None:
        context["evidence_text"] = evidence_text
    source = TextifySource(
        path=path,
        name=_metadata_string(metadata, "name", Path(path).name) or Path(path).name,
        mime_type=_metadata_string(metadata, "mime_type"),
        sha256=_metadata_string(metadata, "sha256", candidate.source_ref.artifact_sha256),
        source_language_hint=_metadata_string(metadata, "source_language_hint"),
        context=context,
    )
    return TextifyRequest(
        request_id=_metadata_string(metadata, "request_id", _stable_request_id("textify", candidate)) or "",
        source=source,
        preferred_output_format=_metadata_string(metadata, "preferred_output_format", DEFAULT_TEXTIFY_OUTPUT_FORMAT)
        or DEFAULT_TEXTIFY_OUTPUT_FORMAT,
        llm_caller=_metadata_string(metadata, "llm_caller"),
    )


def _translation_request_from_candidate(candidate: ProcessCandidate) -> TranslationRequest:
    metadata = candidate.metadata
    return TranslationRequest(
        request_id=_metadata_string(metadata, "request_id", _stable_request_id("translate", candidate)) or "",
        target_language=_metadata_string(metadata, "target_language", DEFAULT_TARGET_LANGUAGE) or DEFAULT_TARGET_LANGUAGE,
        english_confidence_threshold=_metadata_probability(
            metadata,
            "english_confidence_threshold",
            DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD,
        ),
        blocks=_translation_blocks_from_metadata(candidate),
        llm_caller=_metadata_string(metadata, "llm_caller"),
    )


def _translation_blocks_from_metadata(candidate: ProcessCandidate) -> Sequence[Block]:
    blocks = candidate.metadata.get("blocks")
    if blocks is not None:
        if not isinstance(blocks, Sequence) or isinstance(blocks, str | bytes):
            raise ValueError("translation candidate blocks must be a sequence")
        return tuple(Block.from_json(block) for block in blocks)

    text = _metadata_string(candidate.metadata, "text")
    if text is None:
        raise ValueError("translation candidate metadata requires blocks or text")
    context = _metadata_mapping(candidate.metadata, "context", {})
    return (
        Block(
            block_id=1,
            name=_metadata_string(candidate.metadata, "name", "candidate_text") or "candidate_text",
            source_language_hint=_metadata_string(candidate.metadata, "source_language_hint"),
            text=text,
            context=context,
        ),
    )


def _textify_process_status(response: TextifyResponse) -> str:
    status = cast(TextifyStatus, response.source.status)
    return {
        TextifyStatus.CONVERTED: TextifyProcessStatus.CONVERTED.value,
        TextifyStatus.SKIPPED_TEXT_MEDIA: TextifyProcessStatus.ALREADY_TEXT.value,
        TextifyStatus.UNSUPPORTED_MEDIA: TextifyProcessStatus.UNSUPPORTED.value,
        TextifyStatus.NO_TEXT_FOUND: TextifyProcessStatus.NO_TEXT.value,
    }[status]


def _translate_process_status(response: TranslationResponse) -> str:
    if any(block.translation_required for block in response.blocks):
        return TranslateProcessStatus.TRANSLATED.value
    return TranslateProcessStatus.ALREADY_ENGLISH.value


def _artifact_output_ref(stage: str, ledger_tab: str, candidate: ProcessCandidate, artifact: ArtifactRef) -> ProcessRef:
    return ProcessRef(
        stage=stage,
        tab=ledger_tab,
        source=candidate.source,
        artifact_url=artifact.url,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
    )


def _metadata_string(metadata: Mapping[str, JsonValue], key: str, default: str | None = None) -> str | None:
    value = metadata.get(key, default)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _metadata_probability(metadata: Mapping[str, JsonValue], key: str, default: float) -> float:
    value = metadata.get(key, default)
    if not isinstance(value, int | float) or isinstance(value, bool) or not 0 <= value <= 1:
        raise ValueError(f"{key} must be a number between 0 and 1")
    return float(value)


def _metadata_mapping(
    metadata: Mapping[str, JsonValue],
    key: str,
    default: Mapping[str, JsonValue],
) -> Mapping[str, JsonValue]:
    value = metadata.get(key, default)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _stable_request_id(prefix: str, candidate: ProcessCandidate) -> str:
    payload = json.dumps(candidate.to_json(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"
