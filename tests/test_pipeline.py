from dataclasses import FrozenInstanceError

import pytest

import curio.pipeline as pipeline
from curio.pipeline import (
    ArtifactRef,
    Eligibility,
    LedgerTab,
    PersistedOutcome,
    PipelineStage,
    ProcessCandidate,
    Processor,
    ProcessorObject,
    ProcessOutcome,
    ProcessRecord,
    ProcessRef,
    TextifyProcessStatus,
    TranslateProcessStatus,
)


def make_download_ref() -> ProcessRef:
    return ProcessRef(
        stage="download",
        tab="downloads",
        source="x://post/123",
        row_number=7,
        row_url="https://sheets.example/row-7",
        spreadsheet_id="sheet-1",
        sheet_id="tab-1",
        artifact_path="/tmp/artifact.json",
        artifact_sha256="abc123",
    )


def make_text_ref() -> ProcessRef:
    return ProcessRef(
        stage=PipelineStage.TEXTIFY.value,
        tab=LedgerTab.TEXTIFICATIONS.value,
        source="textifications!8",
        row_number=8,
    )


def make_artifact_ref() -> ArtifactRef:
    root_ref = make_download_ref()
    return ArtifactRef(
        kind="translation_response",
        mime_type="application/json",
        path="/tmp/translations/translation.json",
        sha256="def456",
        size_bytes=120,
        source_ref=make_text_ref(),
        imsgx=root_ref,
    )


def make_candidate() -> ProcessCandidate:
    root_ref = make_download_ref()
    return ProcessCandidate(
        source_ref=root_ref,
        imsgx=root_ref,
        source="x://post/123",
        artifact_key="artifact.json",
        metadata={"mime_type": "text/plain"},
    )


def test_pipeline_root_exports_contracts() -> None:
    assert pipeline.__all__ == [
        "ArtifactRef",
        "ArtifactStore",
        "Eligibility",
        "LedgerTab",
        "PipelineStage",
        "PipelineStore",
        "PersistedOutcome",
        "ProcessCandidate",
        "ProcessOutcome",
        "ProcessRecord",
        "ProcessRef",
        "Processor",
        "ProcessorObject",
        "TextifyProcessStatus",
        "TranslateProcessStatus",
    ]


def test_pipeline_enums_are_limited_to_initial_processors() -> None:
    assert PipelineStage.TEXTIFY == "textify"
    assert PipelineStage.TRANSLATE == "translate"
    assert LedgerTab.TEXTIFICATIONS == "textifications"
    assert LedgerTab.TRANSLATIONS == "translations"
    assert TextifyProcessStatus.ALREADY_TEXT == "already_text"
    assert TranslateProcessStatus.ALREADY_ENGLISH == "already_english"


def test_process_ref_serializes_and_validates_identity() -> None:
    ref = make_download_ref()
    payload = ref.to_json()

    assert payload["source"] == "x://post/123"
    assert ProcessRef.from_json(payload) == ref
    assert ProcessRef.from_json({"stage": "download", "tab": "downloads", "source": "source"}).row_number is None

    with pytest.raises(ValueError, match="stage must be a string"):
        ProcessRef(stage=1, tab="downloads", source="source")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stage must not be empty"):
        ProcessRef(stage=" ", tab="downloads", source="source")
    with pytest.raises(ValueError, match="row_number must be a positive integer"):
        ProcessRef(stage="download", tab="downloads", source="source", row_number=0)
    with pytest.raises(ValueError, match="stage is required"):
        ProcessRef.from_json({"tab": "downloads", "source": "source"})


def test_artifact_ref_serializes_lineage() -> None:
    artifact = make_artifact_ref()
    payload = artifact.to_json()

    assert payload["iMsgX"] == make_download_ref().to_json()
    assert ArtifactRef.from_json(payload) == artifact
    assert ArtifactRef.from_json(
        {
            "kind": "textify_response",
            "mime_type": "application/json",
            "url": "https://drive.example/object",
        }
    ).source_ref is None

    with pytest.raises(ValueError, match="artifact ref requires url or path"):
        ArtifactRef(kind="translation_response", mime_type="application/json")
    with pytest.raises(ValueError, match="size_bytes must be a non-negative integer"):
        ArtifactRef(kind="translation_response", mime_type="application/json", path="/tmp/file.json", size_bytes=-1)
    with pytest.raises(ValueError, match="source_ref must be a ProcessRef"):
        ArtifactRef(
            kind="translation_response",
            mime_type="application/json",
            path="/tmp/file.json",
            source_ref="bad-ref",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="imsgx must be a ProcessRef"):
        ArtifactRef(
            kind="translation_response",
            mime_type="application/json",
            path="/tmp/file.json",
            imsgx="bad-ref",  # type: ignore[arg-type]
        )


def test_process_candidate_serializes_and_copies_metadata() -> None:
    candidate = make_candidate()
    payload = candidate.to_json()
    metadata = {"format": "markdown"}
    copied = ProcessCandidate(
        source_ref=candidate.source_ref,
        imsgx=candidate.imsgx,
        source=candidate.source,
        metadata=metadata,
    )

    metadata["format"] = "txt"

    assert ProcessCandidate.from_json(payload) == candidate
    assert copied.metadata == {"format": "markdown"}

    with pytest.raises(ValueError, match="source_ref must be a ProcessRef"):
        ProcessCandidate(
            source_ref="bad-ref",  # type: ignore[arg-type]
            imsgx=candidate.imsgx,
            source="source",
        )
    with pytest.raises(ValueError, match="imsgx must be a ProcessRef"):
        ProcessCandidate(
            source_ref=candidate.source_ref,
            imsgx="bad-ref",  # type: ignore[arg-type]
            source="source",
        )


def test_eligibility_serializes_and_requires_boolean() -> None:
    eligibility = Eligibility(
        eligible=False,
        status=TextifyProcessStatus.UNSUPPORTED.value,
        metadata={"reason": "binary"},
    )

    assert Eligibility.from_json(eligibility.to_json()) == eligibility

    with pytest.raises(ValueError, match="eligible must be a boolean"):
        Eligibility(eligible=1, status="unsupported")


def test_processor_object_and_outcomes_serialize() -> None:
    processor_object = ProcessorObject(payload={"response": {"ok": True}})
    process_outcome = ProcessOutcome(
        status=TranslateProcessStatus.TRANSLATED.value,
        object_=processor_object,
        output_source=make_text_ref(),
        metadata={"blocks": 1},
    )
    persisted_outcome = PersistedOutcome(
        status=process_outcome.status,
        object_=make_artifact_ref(),
        output_source=make_text_ref(),
        metadata=process_outcome.metadata,
    )

    assert ProcessorObject.from_json(processor_object.to_json()) == processor_object
    assert ProcessOutcome.from_json(process_outcome.to_json()) == process_outcome
    assert PersistedOutcome.from_json(persisted_outcome.to_json()) == persisted_outcome

    with pytest.raises(ValueError, match="payload must be an object"):
        ProcessorObject(payload=[])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="object_ must be a ProcessorObject"):
        ProcessOutcome(status="converted", object_="bad-object")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="output_source must be a ProcessRef"):
        ProcessOutcome(status="converted", output_source="bad-ref")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="object_ must be an ArtifactRef"):
        PersistedOutcome(status="converted", object_="bad-object")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="output_source must be a ProcessRef"):
        PersistedOutcome(status="converted", output_source="bad-ref")  # type: ignore[arg-type]


def test_process_record_serializes_compact_row_fields() -> None:
    candidate = make_candidate()
    record = ProcessRecord(
        stage=PipelineStage.TRANSLATE.value,
        ledger_tab=LedgerTab.TRANSLATIONS.value,
        version="translate-v1",
        source_ref=candidate.source_ref,
        imsgx=candidate.imsgx,
        status=TranslateProcessStatus.TRANSLATED.value,
        object_=make_artifact_ref(),
        output_source=make_text_ref(),
        metadata={"request_id": "translate-1"},
    )

    payload = record.to_json()

    assert payload["object"] == make_artifact_ref().to_json()
    assert ProcessRecord.from_json(payload) == record

    with pytest.raises(ValueError, match="source_ref must be a ProcessRef"):
        ProcessRecord(
            stage="translate",
            ledger_tab="translations",
            version="v1",
            source_ref="bad-ref",  # type: ignore[arg-type]
            imsgx=candidate.imsgx,
            status="translated",
        )
    with pytest.raises(ValueError, match="imsgx must be a ProcessRef"):
        ProcessRecord(
            stage="translate",
            ledger_tab="translations",
            version="v1",
            source_ref=candidate.source_ref,
            imsgx="bad-ref",  # type: ignore[arg-type]
            status="translated",
        )
    with pytest.raises(ValueError, match="object_ must be an ArtifactRef"):
        ProcessRecord(
            stage="translate",
            ledger_tab="translations",
            version="v1",
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
            status="translated",
            object_="bad-object",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="output_source must be a ProcessRef"):
        ProcessRecord(
            stage="translate",
            ledger_tab="translations",
            version="v1",
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
            status="translated",
            output_source="bad-ref",  # type: ignore[arg-type]
        )


def test_contract_models_are_frozen() -> None:
    ref = make_download_ref()

    with pytest.raises(FrozenInstanceError):
        ref.source = "new-source"  # type: ignore[misc]


class FakeStore:
    def __init__(self, candidate: ProcessCandidate | None) -> None:
        self.candidate = candidate
        self.records: list[ProcessRecord] = []

    def next_candidate(self, stage: str) -> ProcessCandidate | None:
        assert stage == PipelineStage.TEXTIFY.value
        return self.candidate

    def existing_record(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ProcessRecord | None:
        assert stage == PipelineStage.TEXTIFY.value
        assert ledger_tab == LedgerTab.TEXTIFICATIONS.value
        assert version == "textify-v1"
        assert candidate == self.candidate
        return None

    def append_record(self, record: ProcessRecord) -> ProcessRecord:
        self.records.append(record)
        return record

    def resolve_ref(self, ref: ProcessRef) -> ProcessRef:
        return ref


class FakeArtifactStore:
    def persist_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
        object_: ProcessorObject,
    ) -> ArtifactRef:
        assert stage == PipelineStage.TEXTIFY.value
        assert ledger_tab == LedgerTab.TEXTIFICATIONS.value
        assert version == "textify-v1"
        assert candidate.source == "x://post/123"
        assert object_.payload == {"text": "hello"}
        return ArtifactRef(
            kind="textify_response",
            mime_type=object_.mime_type,
            path="/tmp/textifications/textify.json",
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
        )


class ConcreteProcessor(Processor):
    stage = PipelineStage.TEXTIFY.value
    ledger_tab = LedgerTab.TEXTIFICATIONS.value
    version = "textify-v1"

    def next_candidate(self, store: FakeStore) -> ProcessCandidate | None:
        self.validate_identity()
        return store.next_candidate(self.stage)

    def eligibility(self, candidate: ProcessCandidate) -> Eligibility:
        return Eligibility(eligible=True, status=TextifyProcessStatus.CONVERTED.value)

    def process(self, candidate: ProcessCandidate) -> ProcessOutcome:
        return ProcessOutcome(
            status=TextifyProcessStatus.CONVERTED.value,
            object_=ProcessorObject(payload={"text": "hello"}),
            output_source=candidate.source_ref,
        )

    def persist(
        self,
        candidate: ProcessCandidate,
        outcome: ProcessOutcome,
        artifacts: FakeArtifactStore,
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
        )

    def record(
        self,
        candidate: ProcessCandidate,
        outcome: PersistedOutcome,
        store: FakeStore,
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
            )
        )


def test_processor_abc_defines_lifecycle_shape() -> None:
    processor = ConcreteProcessor()
    store = FakeStore(make_candidate())
    artifact_store = FakeArtifactStore()
    candidate = processor.next_candidate(store)

    assert candidate is not None
    assert store.existing_record(
        stage=processor.stage,
        ledger_tab=processor.ledger_tab,
        version=processor.version,
        candidate=candidate,
    ) is None
    assert processor.eligibility(candidate).eligible is True

    outcome = processor.process(candidate)
    persisted = processor.persist(candidate, outcome, artifact_store)
    record = processor.record(candidate, persisted, store)

    assert record.object_ == persisted.object_
    assert store.records == [record]


class InvalidIdentityProcessor(ConcreteProcessor):
    stage = ""


def test_processor_identity_validation_rejects_empty_values() -> None:
    with pytest.raises(ValueError, match="stage must not be empty"):
        InvalidIdentityProcessor().validate_identity()


def test_abstract_processor_methods_raise_when_called_directly() -> None:
    processor = ConcreteProcessor()
    candidate = make_candidate()

    with pytest.raises(NotImplementedError):
        Processor.next_candidate(processor, FakeStore(candidate))
    with pytest.raises(NotImplementedError):
        Processor.eligibility(processor, candidate)
    with pytest.raises(NotImplementedError):
        Processor.process(processor, candidate)
    with pytest.raises(NotImplementedError):
        Processor.persist(processor, candidate, ProcessOutcome(status="converted"), FakeArtifactStore())
    with pytest.raises(NotImplementedError):
        Processor.record(processor, candidate, PersistedOutcome(status="converted"), FakeStore(candidate))
