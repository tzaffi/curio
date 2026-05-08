from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from curio.pipeline.memory import FAILED_STATUS
from curio.pipeline.models import (
    ArtifactRef,
    ArtifactStore,
    LedgerTab,
    PersistedOutcome,
    PipelineStage,
    PipelineStore,
    ProcessCandidate,
    Processor,
    ProcessRecord,
    ProcessRef,
)

SUPPORTED_PIPELINE_STAGES: Final = frozenset({PipelineStage.TEXTIFY.value, PipelineStage.TRANSLATE.value})


class ProcessorRunStatus(StrEnum):
    NO_CANDIDATE = "no_candidate"
    ALREADY_HANDLED = "already_handled"
    RECORDED = "recorded"
    FAILED = "failed"


PROGRESSING_PROCESSOR_RUN_STATUSES: Final = frozenset(
    {ProcessorRunStatus.RECORDED, ProcessorRunStatus.FAILED}
)


@dataclass(frozen=True, slots=True)
class ProcessorRunResult:
    stage: str
    status: ProcessorRunStatus
    candidate: ProcessCandidate | None = None
    record: ProcessRecord | None = None
    existing_record: ProcessRecord | None = None


PipelineProgressCallback = Callable[[ProcessorRunResult], None]
_CandidateIdentity = tuple[str, ProcessRef, ProcessRef]


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    iterations: int
    processor_results: tuple[ProcessorRunResult, ...]

    @property
    def made_progress(self) -> bool:
        return any(result.status in PROGRESSING_PROCESSOR_RUN_STATUSES for result in self.processor_results)


def run_processor_once(
    processor: Processor,
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
) -> ProcessorRunResult:
    return _run_processor_once(processor, store=store, artifacts=artifacts)


def _run_processor_once(
    processor: Processor,
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
    seen_candidate_identities: set[_CandidateIdentity] | None = None,
) -> ProcessorRunResult:
    _validate_supported_processor(processor)
    candidate = processor.next_candidate(store)
    if candidate is None:
        return ProcessorRunResult(stage=processor.stage, status=ProcessorRunStatus.NO_CANDIDATE)
    if seen_candidate_identities is not None:
        _record_unseen_candidate(processor.stage, candidate, seen_candidate_identities)

    existing_record = store.existing_record(
        stage=processor.stage,
        ledger_tab=processor.ledger_tab,
        version=processor.version,
        candidate=candidate,
    )
    if existing_record is not None:
        return ProcessorRunResult(
            stage=processor.stage,
            status=ProcessorRunStatus.ALREADY_HANDLED,
            candidate=candidate,
            existing_record=existing_record,
        )

    discard_object_on_stage_failure = False

    try:
        eligibility = processor.eligibility(candidate)
        if not eligibility.eligible:
            persisted = PersistedOutcome(
                status=eligibility.status,
                output_source=candidate.source_ref,
                metadata=eligibility.metadata,
            )
        else:
            existing_object = artifacts.existing_object(
                stage=processor.stage,
                ledger_tab=processor.ledger_tab,
                version=processor.version,
                candidate=candidate,
            )
            if existing_object is not None:
                persisted = PersistedOutcome(
                    status=eligibility.status,
                    object_=existing_object,
                    output_source=_artifact_output_ref(processor, candidate, existing_object),
                    metadata=eligibility.metadata,
                )
            else:
                outcome = processor.process(candidate)
                persisted = processor.persist(candidate, outcome, artifacts)
                discard_object_on_stage_failure = persisted.object_ is not None
    except Exception as exc:
        record = processor.record(candidate, _failed_outcome(exc), store)
        return ProcessorRunResult(
            stage=processor.stage,
            status=ProcessorRunStatus.FAILED,
            candidate=candidate,
            record=record,
        )
    try:
        record = processor.record(candidate, persisted, store)
    except Exception:
        if discard_object_on_stage_failure and persisted.object_ is not None:
            artifacts.discard_object(persisted.object_)
        raise
    return ProcessorRunResult(
        stage=processor.stage,
        status=ProcessorRunStatus.RECORDED,
        candidate=candidate,
        record=record,
    )


def run_stage(
    processor: Processor,
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
    limit: int,
    progress_callback: PipelineProgressCallback | None = None,
) -> PipelineRunResult:
    if limit < 1:
        raise ValueError("limit must be a positive integer")

    results: list[ProcessorRunResult] = []
    seen_candidate_identities: set[_CandidateIdentity] = set()
    try:
        for _ in range(limit):
            result = _run_processor_once(
                processor,
                store=store,
                artifacts=artifacts,
                seen_candidate_identities=seen_candidate_identities,
            )
            results.append(result)
            _notify_progress(progress_callback, result)
            if result.status not in PROGRESSING_PROCESSOR_RUN_STATUSES:
                break
        store.flush_records()
    except Exception:
        _discard_current_run(results, store=store, artifacts=artifacts)
        raise
    return PipelineRunResult(
        iterations=sum(result.status in PROGRESSING_PROCESSOR_RUN_STATUSES for result in results),
        processor_results=tuple(results),
    )


def run_artifact_through(
    processors: Sequence[Processor],
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
    limit: int,
    progress_callback: PipelineProgressCallback | None = None,
) -> PipelineRunResult:
    if not processors:
        raise ValueError("processors must not be empty")
    if limit < 1:
        raise ValueError("limit must be a positive integer")
    for processor in processors:
        _validate_supported_processor(processor)

    results: list[ProcessorRunResult] = []
    seen_candidate_identities: set[_CandidateIdentity] = set()
    iterations = 0
    try:
        for _ in range(limit):
            iteration_results: list[ProcessorRunResult] = []
            for processor in processors:
                result = _run_processor_once(
                    processor,
                    store=store,
                    artifacts=artifacts,
                    seen_candidate_identities=seen_candidate_identities,
                )
                results.append(result)
                iteration_results.append(result)
                _notify_progress(progress_callback, result)
            if not any(result.status in PROGRESSING_PROCESSOR_RUN_STATUSES for result in iteration_results):
                break
            iterations += 1
        store.flush_records()
    except Exception:
        _discard_current_run(results, store=store, artifacts=artifacts)
        raise

    return PipelineRunResult(iterations=iterations, processor_results=tuple(results))


def _notify_progress(
    progress_callback: PipelineProgressCallback | None,
    result: ProcessorRunResult,
) -> None:
    if progress_callback is not None:
        progress_callback(result)


def _record_unseen_candidate(
    stage: str,
    candidate: ProcessCandidate,
    seen_candidate_identities: set[_CandidateIdentity],
) -> None:
    identity = (stage, candidate.source_ref, candidate.imsgx)
    if identity in seen_candidate_identities:
        downloads_row = candidate.source_ref.row_number
        row_detail = "-" if downloads_row is None else str(downloads_row)
        raise RuntimeError(
            "pipeline selected the same candidate twice in one run: "
            f"stage={stage} downloads_row={row_detail} source={candidate.source}"
        )
    seen_candidate_identities.add(identity)


def _discard_current_run(
    results: Sequence[ProcessorRunResult],
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
) -> None:
    for result in results:
        if result.status == ProcessorRunStatus.RECORDED and result.record is not None and result.record.object_ is not None:
            artifacts.discard_object(result.record.object_)
    store.discard_staged_records()


def _validate_supported_processor(processor: Processor) -> None:
    processor.validate_identity()
    if processor.stage not in SUPPORTED_PIPELINE_STAGES:
        raise ValueError(f"unsupported pipeline stage for current scope: {processor.stage}")
    expected_tabs = {
        PipelineStage.TEXTIFY.value: LedgerTab.TEXTIFICATIONS.value,
        PipelineStage.TRANSLATE.value: LedgerTab.TRANSLATIONS.value,
    }
    if processor.ledger_tab != expected_tabs[processor.stage]:
        raise ValueError(f"ledger_tab does not match stage {processor.stage}: {processor.ledger_tab}")


def _artifact_output_ref(processor: Processor, candidate: ProcessCandidate, artifact: ArtifactRef) -> ProcessRef:
    return ProcessRef(
        stage=processor.stage,
        tab=processor.ledger_tab,
        source=candidate.source,
        artifact_url=artifact.url,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
    )


def _failed_outcome(exc: Exception) -> PersistedOutcome:
    return PersistedOutcome(
        status=FAILED_STATUS,
        metadata={
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
    )
