from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from curio.pipeline.memory import FAILED_STATUS
from curio.pipeline.models import (
    ArtifactStore,
    LedgerTab,
    PersistedOutcome,
    PipelineStage,
    PipelineStore,
    ProcessCandidate,
    Processor,
    ProcessRecord,
)

SUPPORTED_PIPELINE_STAGES: Final = frozenset({PipelineStage.TEXTIFY.value, PipelineStage.TRANSLATE.value})


class ProcessorRunStatus(StrEnum):
    NO_CANDIDATE = "no_candidate"
    ALREADY_HANDLED = "already_handled"
    RECORDED = "recorded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProcessorRunResult:
    stage: str
    status: ProcessorRunStatus
    candidate: ProcessCandidate | None = None
    record: ProcessRecord | None = None
    existing_record: ProcessRecord | None = None


@dataclass(frozen=True, slots=True)
class PipelineRunResult:
    iterations: int
    processor_results: tuple[ProcessorRunResult, ...]

    @property
    def made_progress(self) -> bool:
        return any(result.status in {ProcessorRunStatus.RECORDED, ProcessorRunStatus.FAILED} for result in self.processor_results)


def run_processor_once(
    processor: Processor,
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
) -> ProcessorRunResult:
    _validate_supported_processor(processor)
    candidate = processor.next_candidate(store)
    if candidate is None:
        return ProcessorRunResult(stage=processor.stage, status=ProcessorRunStatus.NO_CANDIDATE)

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

    try:
        eligibility = processor.eligibility(candidate)
        if not eligibility.eligible:
            record = processor.record(
                candidate,
                PersistedOutcome(
                    status=eligibility.status,
                    output_source=candidate.source_ref,
                    metadata=eligibility.metadata,
                ),
                store,
            )
            return ProcessorRunResult(
                stage=processor.stage,
                status=ProcessorRunStatus.RECORDED,
                candidate=candidate,
                record=record,
            )

        outcome = processor.process(candidate)
        persisted = processor.persist(candidate, outcome, artifacts)
        record = processor.record(candidate, persisted, store)
        return ProcessorRunResult(
            stage=processor.stage,
            status=ProcessorRunStatus.RECORDED,
            candidate=candidate,
            record=record,
        )
    except Exception as exc:
        record = processor.record(candidate, _failed_outcome(exc), store)
        return ProcessorRunResult(
            stage=processor.stage,
            status=ProcessorRunStatus.FAILED,
            candidate=candidate,
            record=record,
        )


def run_stage(
    processor: Processor,
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
    limit: int,
) -> PipelineRunResult:
    if limit < 1:
        raise ValueError("limit must be a positive integer")

    results: list[ProcessorRunResult] = []
    for _ in range(limit):
        result = run_processor_once(processor, store=store, artifacts=artifacts)
        results.append(result)
        if result.status not in {ProcessorRunStatus.RECORDED, ProcessorRunStatus.FAILED}:
            break
    return PipelineRunResult(
        iterations=sum(result.status in {ProcessorRunStatus.RECORDED, ProcessorRunStatus.FAILED} for result in results),
        processor_results=tuple(results),
    )


def run_artifact_through(
    processors: Sequence[Processor],
    *,
    store: PipelineStore,
    artifacts: ArtifactStore,
    limit: int,
) -> PipelineRunResult:
    if not processors:
        raise ValueError("processors must not be empty")
    if limit < 1:
        raise ValueError("limit must be a positive integer")
    for processor in processors:
        _validate_supported_processor(processor)

    results: list[ProcessorRunResult] = []
    iterations = 0
    for _ in range(limit):
        iteration_results: list[ProcessorRunResult] = []
        for processor in processors:
            result = run_processor_once(processor, store=store, artifacts=artifacts)
            results.append(result)
            iteration_results.append(result)
        if not any(result.status in {ProcessorRunStatus.RECORDED, ProcessorRunStatus.FAILED} for result in iteration_results):
            break
        iterations += 1

    return PipelineRunResult(iterations=iterations, processor_results=tuple(results))


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


def _failed_outcome(exc: Exception) -> PersistedOutcome:
    return PersistedOutcome(
        status=FAILED_STATUS,
        metadata={
            "error_type": type(exc).__name__,
            "error": str(exc),
        },
    )
