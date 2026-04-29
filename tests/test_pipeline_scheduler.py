import json
from pathlib import Path

import pytest

import curio.pipeline as pipeline
from curio.config import PipelineConfig
from curio.pipeline import (
    Eligibility,
    InMemoryArtifactStore,
    InMemoryPipelineStore,
    LedgerTab,
    LocalArtifactStore,
    PersistedOutcome,
    PipelineStage,
    PipelineStore,
    ProcessCandidate,
    Processor,
    ProcessorObject,
    ProcessorRunStatus,
    ProcessOutcome,
    ProcessRecord,
    ProcessRef,
    TextifyProcessStatus,
    TranslateProcessStatus,
    run_artifact_through,
    run_processor_once,
    run_stage,
)

DEFAULT_ARTIFACT_KEY = object()


def make_download_ref(
    source: str = "x://post/123",
    row_number: int | None = 7,
    artifact_path: str | None = None,
) -> ProcessRef:
    return ProcessRef(
        stage="download",
        tab="downloads",
        source=source,
        row_number=row_number,
        artifact_path=artifact_path,
        artifact_sha256=f"sha-{row_number}",
    )


def make_candidate(
    source: str = "x://post/123",
    row_number: int | None = 7,
    artifact_path: str | None = None,
    artifact_key: str | None | object = DEFAULT_ARTIFACT_KEY,
) -> ProcessCandidate:
    root_ref = make_download_ref(source, row_number, artifact_path)
    resolved_artifact_key: str | None
    if artifact_key is DEFAULT_ARTIFACT_KEY:
        resolved_artifact_key = f"artifact-{row_number}.json"
    else:
        assert artifact_key is None or isinstance(artifact_key, str)
        resolved_artifact_key = artifact_key
    return ProcessCandidate(
        source_ref=root_ref,
        imsgx=root_ref,
        source=source,
        artifact_key=resolved_artifact_key,
        metadata={"row": row_number},
    )


class StageProcessor(Processor):
    version = "processor-v1"

    def __init__(
        self,
        *,
        stage: str = PipelineStage.TEXTIFY.value,
        ledger_tab: str = LedgerTab.TEXTIFICATIONS.value,
        eligible: bool = True,
        process_status: str = TextifyProcessStatus.CONVERTED.value,
        skip_status: str = TextifyProcessStatus.ALREADY_TEXT.value,
        fail_sources: set[str] | None = None,
        enqueue_translate: bool = False,
    ) -> None:
        self.stage = stage
        self.ledger_tab = ledger_tab
        self.eligible = eligible
        self.process_status = process_status
        self.skip_status = skip_status
        self.fail_sources = set() if fail_sources is None else fail_sources
        self.enqueue_translate = enqueue_translate

    def next_candidate(self, store: PipelineStore) -> ProcessCandidate | None:
        return store.next_candidate(self.stage)

    def eligibility(self, candidate: ProcessCandidate) -> Eligibility:
        return Eligibility(
            eligible=self.eligible,
            status=self.process_status if self.eligible else self.skip_status,
            metadata={"source": candidate.source},
        )

    def process(self, candidate: ProcessCandidate) -> ProcessOutcome:
        if candidate.source in self.fail_sources:
            raise RuntimeError(f"planned failure for {candidate.source}")
        return ProcessOutcome(
            status=self.process_status,
            object_=ProcessorObject(payload={"source": candidate.source}),
            output_source=candidate.source_ref,
            metadata={"processed": True},
        )

    def persist(
        self,
        candidate: ProcessCandidate,
        outcome: ProcessOutcome,
        artifacts: InMemoryArtifactStore,
    ) -> PersistedOutcome:
        assert outcome.object_ is not None
        return PersistedOutcome(
            status=outcome.status,
            object_=artifacts.persist_object(
                stage=self.stage,
                ledger_tab=self.ledger_tab,
                version=self.version,
                candidate=candidate,
                object_=outcome.object_,
            ),
            output_source=outcome.output_source,
            metadata=outcome.metadata,
        )

    def record(
        self,
        candidate: ProcessCandidate,
        outcome: PersistedOutcome,
        store: PipelineStore,
    ) -> ProcessRecord:
        record = store.append_record(
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
        if self.enqueue_translate and isinstance(store, InMemoryPipelineStore):
            output_ref = outcome.output_source if outcome.output_source is not None else candidate.source_ref
            store.add_candidate(
                PipelineStage.TRANSLATE.value,
                ProcessCandidate(
                    source_ref=output_ref,
                    imsgx=candidate.imsgx,
                    source=f"{candidate.source}#textified",
                    metadata={"from_stage": self.stage},
                ),
            )
        return record


class StaticExistingStore:
    def __init__(self, candidate: ProcessCandidate, record: ProcessRecord) -> None:
        self.candidate = candidate
        self.record = record
        self.appended: list[ProcessRecord] = []

    def next_candidate(self, stage: str) -> ProcessCandidate | None:
        return self.candidate

    def existing_record(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ProcessRecord | None:
        assert candidate == self.candidate
        assert (stage, ledger_tab, version) == (self.record.stage, self.record.ledger_tab, self.record.version)
        return self.record

    def append_record(self, record: ProcessRecord) -> ProcessRecord:
        self.appended.append(record)
        return record

    def resolve_ref(self, ref: ProcessRef) -> ProcessRef:
        return ref


def test_pipeline_root_exports_scheduler_contracts() -> None:
    assert "InMemoryArtifactStore" in pipeline.__all__
    assert "InMemoryPipelineStore" in pipeline.__all__
    assert "ProcessorRunStatus" in pipeline.__all__
    assert "run_artifact_through" in pipeline.__all__
    assert "run_processor_once" in pipeline.__all__
    assert "run_stage" in pipeline.__all__


def test_in_memory_store_selects_unhandled_candidates_and_skips_failures_by_default() -> None:
    first = make_candidate("x://post/1", 1)
    second = make_candidate("x://post/2", 2)
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [first, second]})

    assert store.next_candidate(PipelineStage.TEXTIFY.value) == first

    failed_record = ProcessRecord(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        source_ref=first.source_ref,
        imsgx=first.imsgx,
        status=TextifyProcessStatus.FAILED.value,
    )
    store.append_record(failed_record)

    assert store.existing_record(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=first,
    ) is None
    assert store.next_candidate(PipelineStage.TEXTIFY.value) == second
    assert store.resolve_ref(second.source_ref) == second.source_ref

    terminal_record = ProcessRecord(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        source_ref=second.source_ref,
        imsgx=second.imsgx,
        status=TextifyProcessStatus.CONVERTED.value,
    )
    store.append_record(terminal_record)

    assert store.existing_record(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=second,
    ) == terminal_record
    assert store.next_candidate(PipelineStage.TEXTIFY.value) is None
    assert store.records == (failed_record, terminal_record)


def test_in_memory_artifact_store_persists_lineage_envelope() -> None:
    candidate = make_candidate()
    object_ = ProcessorObject(payload={"text": "hello"})
    store = InMemoryArtifactStore()

    ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=object_,
    )
    objects = store.objects

    assert ref.kind == "textify_object"
    assert ref.path is not None
    assert ref.path in objects
    assert objects[ref.path]["source_ref"] == candidate.source_ref.to_json()
    assert objects[ref.path]["object"] == {"text": "hello"}
    assert ref.sha256 is not None
    assert ref.size_bytes is not None and ref.size_bytes > 0

    objects[ref.path] = {"mutated": True}

    assert store.objects[ref.path]["object"] == {"text": "hello"}


def test_local_artifact_store_writes_textify_artifact_from_imsgx_source_stem(tmp_path: Path) -> None:
    candidate = make_candidate(
        artifact_path="/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0008-x1-image-203-photo-1.png"
    )
    object_ = ProcessorObject(payload={"text": "hello"})
    store = LocalArtifactStore(tmp_path)

    first_ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=object_,
    )
    second_ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=object_,
    )

    assert first_ref == second_ref
    assert first_ref.path is not None
    persisted_path = Path(first_ref.path)
    assert persisted_path == tmp_path / "textifications/imsgx-r0008-textify-x1-image-203-photo-1.json"
    envelope = json.loads(persisted_path.read_text(encoding="utf-8"))
    assert envelope["version"] == "processor-v1"
    assert envelope["source_ref"] == candidate.source_ref.to_json()
    assert envelope["iMsgX"] == candidate.imsgx.to_json()
    assert envelope["object"] == {"text": "hello"}
    assert first_ref.sha256 is not None
    assert first_ref.size_bytes == persisted_path.stat().st_size
    assert first_ref.source_ref == candidate.source_ref
    assert first_ref.imsgx == candidate.imsgx


def test_local_artifact_store_writes_translate_artifact_from_imsgx_artifact_key(tmp_path: Path) -> None:
    candidate = make_candidate(
        source="tweet://bcherny/status/2017",
        row_number=2,
        artifact_key="imsgx-r0002-text-tweet-bcherny-status-2017.json",
    )
    store = LocalArtifactStore(tmp_path)

    ref = store.persist_object(
        stage=PipelineStage.TRANSLATE.value,
        ledger_tab=LedgerTab.TRANSLATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=ProcessorObject(payload={"translated_text": "hello"}),
    )

    assert ref.path == str(tmp_path / "translations/imsgx-r0002-translate-text-tweet-bcherny-status-2017.json")


def test_local_artifact_store_synthesizes_imsgx_filename_from_row_and_source(tmp_path: Path) -> None:
    candidate = make_candidate(source="https://example.com/Some Long Source?!", row_number=11, artifact_key=None)
    store = LocalArtifactStore(tmp_path)

    ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=ProcessorObject(payload={"text": "hello"}),
    )

    assert ref.path == str(tmp_path / "textifications/imsgx-r0011-textify-https-example-com-some-long-source.json")


def test_local_artifact_store_uses_hash_filename_when_source_identity_is_missing(tmp_path: Path) -> None:
    candidate = make_candidate(source="x://post/123", row_number=None, artifact_key=None)
    store = LocalArtifactStore(tmp_path)

    ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=ProcessorObject(payload={"text": "hello"}),
    )

    assert ref.path is not None
    persisted_path = Path(ref.path)
    assert persisted_path.parent == tmp_path / LedgerTab.TEXTIFICATIONS.value
    assert persisted_path.name.startswith("imsgx-textify-")
    assert persisted_path.name.endswith(".json")


def test_local_artifact_store_rejects_changed_content_for_same_path(tmp_path: Path) -> None:
    candidate = make_candidate(
        artifact_path="/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0008-x1-image-203-photo-1.png"
    )
    store = LocalArtifactStore(tmp_path)
    store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
        object_=ProcessorObject(payload={"text": "hello"}),
    )

    with pytest.raises(FileExistsError, match="different content"):
        store.persist_object(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab=LedgerTab.TEXTIFICATIONS.value,
            version="processor-v1",
            candidate=candidate,
            object_=ProcessorObject(payload={"text": "changed"}),
        )


def test_local_artifact_store_uses_pipeline_config_effective_artifact_root(tmp_path: Path) -> None:
    store = LocalArtifactStore.from_config(PipelineConfig(downloads_dir=tmp_path / "downloads"))

    assert store.root == tmp_path


def test_run_processor_once_records_eligible_output() -> None:
    candidate = make_candidate()
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})
    artifacts = InMemoryArtifactStore()
    processor = StageProcessor()

    result = run_processor_once(processor, store=store, artifacts=artifacts)

    assert result.status == ProcessorRunStatus.RECORDED
    assert result.candidate == candidate
    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.CONVERTED.value
    assert result.record.object_ is not None
    assert result.record.object_.path in artifacts.objects


def test_run_processor_once_records_skipped_output_source_without_artifact() -> None:
    candidate = make_candidate()
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})
    processor = StageProcessor(eligible=False)

    result = run_processor_once(processor, store=store, artifacts=InMemoryArtifactStore())

    assert result.status == ProcessorRunStatus.RECORDED
    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.ALREADY_TEXT.value
    assert result.record.object_ is None
    assert result.record.output_source == candidate.source_ref
    assert result.record.metadata == {"source": candidate.source}


def test_run_processor_once_noops_when_terminal_record_already_exists() -> None:
    candidate = make_candidate()
    existing_record = ProcessRecord(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        source_ref=candidate.source_ref,
        imsgx=candidate.imsgx,
        status=TextifyProcessStatus.CONVERTED.value,
    )
    store = StaticExistingStore(candidate, existing_record)

    result = run_processor_once(StageProcessor(), store=store, artifacts=InMemoryArtifactStore())

    assert result.status == ProcessorRunStatus.ALREADY_HANDLED
    assert result.existing_record == existing_record
    assert store.appended == []


def test_run_processor_once_returns_no_candidate() -> None:
    store = InMemoryPipelineStore()

    result = run_processor_once(StageProcessor(), store=store, artifacts=InMemoryArtifactStore())

    assert result.status == ProcessorRunStatus.NO_CANDIDATE
    assert result.candidate is None
    assert result.record is None


def test_run_stage_records_failure_and_continues_to_unrelated_source() -> None:
    first = make_candidate("x://post/1", 1)
    second = make_candidate("x://post/2", 2)
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [first, second]})
    processor = StageProcessor(fail_sources={first.source})

    result = run_stage(processor, store=store, artifacts=InMemoryArtifactStore(), limit=2)

    assert result.iterations == 2
    assert [processor_result.status for processor_result in result.processor_results] == [
        ProcessorRunStatus.FAILED,
        ProcessorRunStatus.RECORDED,
    ]
    assert [record.status for record in store.records] == [
        TextifyProcessStatus.FAILED.value,
        TextifyProcessStatus.CONVERTED.value,
    ]
    assert store.records[0].metadata == {
        "error_type": "RuntimeError",
        "error": "planned failure for x://post/1",
    }
    assert result.made_progress is True


def test_run_stage_stops_cleanly_on_no_work() -> None:
    result = run_stage(StageProcessor(), store=InMemoryPipelineStore(), artifacts=InMemoryArtifactStore(), limit=10)

    assert result.iterations == 0
    assert result.processor_results[0].status == ProcessorRunStatus.NO_CANDIDATE
    assert result.made_progress is False


def test_run_artifact_through_runs_textify_then_translate_and_stops_after_translate() -> None:
    source = make_candidate("x://post/1", 1)
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [source]})
    textify = StageProcessor(enqueue_translate=True)
    translate = StageProcessor(
        stage=PipelineStage.TRANSLATE.value,
        ledger_tab=LedgerTab.TRANSLATIONS.value,
        process_status=TranslateProcessStatus.TRANSLATED.value,
        skip_status=TranslateProcessStatus.ALREADY_ENGLISH.value,
    )

    result = run_artifact_through([textify, translate], store=store, artifacts=InMemoryArtifactStore(), limit=2)

    assert result.iterations == 1
    assert [processor_result.stage for processor_result in result.processor_results] == [
        PipelineStage.TEXTIFY.value,
        PipelineStage.TRANSLATE.value,
        PipelineStage.TEXTIFY.value,
        PipelineStage.TRANSLATE.value,
    ]
    assert [record.stage for record in store.records] == [
        PipelineStage.TEXTIFY.value,
        PipelineStage.TRANSLATE.value,
    ]
    assert [record.status for record in store.records] == [
        TextifyProcessStatus.CONVERTED.value,
        TranslateProcessStatus.TRANSLATED.value,
    ]


def test_run_artifact_through_stops_cleanly_on_no_work() -> None:
    result = run_artifact_through(
        [
            StageProcessor(),
            StageProcessor(
                stage=PipelineStage.TRANSLATE.value,
                ledger_tab=LedgerTab.TRANSLATIONS.value,
                process_status=TranslateProcessStatus.TRANSLATED.value,
            ),
        ],
        store=InMemoryPipelineStore(),
        artifacts=InMemoryArtifactStore(),
        limit=3,
    )

    assert result.iterations == 0
    assert [processor_result.status for processor_result in result.processor_results] == [
        ProcessorRunStatus.NO_CANDIDATE,
        ProcessorRunStatus.NO_CANDIDATE,
    ]


def test_scheduler_rejects_out_of_scope_or_mismatched_processors() -> None:
    with pytest.raises(ValueError, match="unsupported pipeline stage"):
        run_processor_once(
            StageProcessor(stage="dossier", ledger_tab="dossiers"),
            store=InMemoryPipelineStore(),
            artifacts=InMemoryArtifactStore(),
        )

    with pytest.raises(ValueError, match="ledger_tab does not match"):
        run_processor_once(
            StageProcessor(stage=PipelineStage.TEXTIFY.value, ledger_tab=LedgerTab.TRANSLATIONS.value),
            store=InMemoryPipelineStore(),
            artifacts=InMemoryArtifactStore(),
        )


def test_scheduler_rejects_invalid_limits_and_empty_pipeline() -> None:
    with pytest.raises(ValueError, match="limit must be a positive integer"):
        run_stage(StageProcessor(), store=InMemoryPipelineStore(), artifacts=InMemoryArtifactStore(), limit=0)

    with pytest.raises(ValueError, match="processors must not be empty"):
        run_artifact_through([], store=InMemoryPipelineStore(), artifacts=InMemoryArtifactStore(), limit=1)

    with pytest.raises(ValueError, match="limit must be a positive integer"):
        run_artifact_through([StageProcessor()], store=InMemoryPipelineStore(), artifacts=InMemoryArtifactStore(), limit=0)
