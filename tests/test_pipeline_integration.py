from collections.abc import Mapping
from pathlib import Path
from typing import cast

from curio.llm_caller import LlmUsage
from curio.pipeline import (
    InMemoryArtifactStore,
    InMemoryPipelineStore,
    PipelineStage,
    ProcessCandidate,
    ProcessorRunStatus,
    ProcessRecord,
    ProcessRef,
    TextifyProcessor,
    TextifyProcessStatus,
    TranslateProcessor,
    TranslateProcessStatus,
    run_artifact_through,
)
from curio.pipeline.models import JsonObject, JsonValue
from curio.textify import (
    SuggestedTextFile,
    TextifiedSource,
    TextifyRequest,
    TextifyResponse,
    TextifyStatus,
)
from curio.translate import (
    Block,
    LlmSummary,
    TranslatedBlock,
    TranslationRequest,
    TranslationResponse,
)
from textify_smoke_helpers import (
    TEXTIFY_SMOKE_CASES,
    TEXTIFY_SMOKE_FIXTURE_ROOT,
    TextifySmokeCase,
)


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=10,
        cached_input_tokens=0,
        output_tokens=5,
        reasoning_tokens=None,
        total_tokens=15,
        metered_objects=[],
        started_at="2026-04-29T00:00:00Z",
        completed_at="2026-04-29T00:00:01Z",
        wall_seconds=1,
        thinking_seconds=None,
    )


def smoke_case(case_id: str) -> TextifySmokeCase:
    return next(case for case in TEXTIFY_SMOKE_CASES if case.case_id == case_id)


def fixture_path(case: TextifySmokeCase) -> Path:
    assert case.fixture_path is not None
    return TEXTIFY_SMOKE_FIXTURE_ROOT / case.fixture_path


def download_candidate(
    *,
    label: str,
    case: TextifySmokeCase,
    row_number: int,
    evidence_text: str | None = None,
    source_language_hint: str | None = None,
    force_textify_failure: bool = False,
) -> ProcessCandidate:
    path = fixture_path(case)
    source = f"fixture://{label}"
    source_ref = ProcessRef(
        stage="download",
        tab="downloads",
        source=source,
        row_number=row_number,
        artifact_path=str(path),
        artifact_sha256=case.fixture_sha256,
    )
    metadata: dict[str, JsonValue] = {
        "path": str(path),
        "name": path.name,
        "mime_type": case.mime_type,
        "sha256": case.fixture_sha256,
        "preferred_output_format": case.preferred_output_format,
        "fixture_case_id": case.case_id,
        "pipeline_label": label,
        "request_id": f"textify-{label}",
        "context": {
            "fixture_case_id": case.case_id,
            "pipeline_label": label,
        },
    }
    if evidence_text is not None:
        metadata["evidence_text"] = evidence_text
    if source_language_hint is not None:
        metadata["source_language_hint"] = source_language_hint
    if force_textify_failure:
        metadata["force_textify_failure"] = True
        cast(dict[str, JsonValue], metadata["context"])["force_textify_failure"] = True
    return ProcessCandidate(
        source_ref=source_ref,
        imsgx=source_ref,
        source=source,
        artifact_key=case.source_basenames[0] if case.source_basenames else path.name,
        metadata=metadata,
    )


class OfflineTextifyService:
    def __init__(self) -> None:
        self.requests: list[TextifyRequest] = []

    def textify(self, request: TextifyRequest) -> TextifyResponse:
        self.requests.append(request)
        if request.source.context.get("force_textify_failure") is True:
            raise RuntimeError("planned offline textify provider failure")

        case = smoke_case(cast(str, request.source.context["fixture_case_id"]))
        status = TextifyStatus(case.expected_status)
        suggested_files = (
            [
                SuggestedTextFile(
                    suggested_path=suggested_path,
                    output_format=_suggested_output_format(suggested_path, case.expected_output_format),
                    text=case.ground_truth_text,
                )
                for suggested_path in case.expected_suggested_paths
            ]
            if status == TextifyStatus.CONVERTED
            else []
        )
        return TextifyResponse(
            request_id=request.request_id,
            source=TextifiedSource(
                name=request.source.name,
                input_mime_type=request.source.mime_type,
                source_sha256=request.source.sha256,
                textification_required=status != TextifyStatus.SKIPPED_TEXT_MEDIA,
                status=status,
                suggested_files=suggested_files,
                warnings=[],
            ),
            warnings=[],
        )


class OfflineTranslationService:
    def __init__(self) -> None:
        self.requests: list[TranslationRequest] = []

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        self.requests.append(request)
        return TranslationResponse(
            request_id=request.request_id,
            blocks=[_translated_block(block) for block in request.blocks],
            llm=LlmSummary(provider="codex_cli", model="offline-fake", usage=make_usage()),
            warnings=[],
        )


class OfflineArtifactThroughStore(InMemoryPipelineStore):
    def __init__(
        self,
        textify_candidates: list[ProcessCandidate],
        artifacts: InMemoryArtifactStore,
    ) -> None:
        super().__init__({PipelineStage.TEXTIFY.value: textify_candidates})
        self._artifacts = artifacts
        self._textify_candidates = {candidate.source_ref: candidate for candidate in textify_candidates}

    def append_record(self, record: ProcessRecord) -> ProcessRecord:
        appended = super().append_record(record)
        if record.stage == PipelineStage.TEXTIFY.value and record.output_source is not None:
            self.add_candidate(
                PipelineStage.TRANSLATE.value,
                _translate_candidate_from_textify_record(record, self._textify_candidates[record.source_ref], self._artifacts),
            )
        return appended


def _suggested_output_format(suggested_path: str, expected_output_format: str) -> str:
    if expected_output_format != "mixed":
        return expected_output_format
    return "txt" if suggested_path.endswith((".log", ".txt")) else "markdown"


def _translate_candidate_from_textify_record(
    record: ProcessRecord,
    original: ProcessCandidate,
    artifacts: InMemoryArtifactStore,
) -> ProcessCandidate:
    assert record.output_source is not None
    label = cast(str, original.metadata["pipeline_label"])
    if record.status == TextifyProcessStatus.CONVERTED.value:
        assert record.object_ is not None
        assert record.object_.path is not None
        envelope = artifacts.objects[record.object_.path]
        textify_response = TextifyResponse.from_json(envelope["object"])
        metadata: dict[str, JsonValue] = {
            "blocks": [
                Block(
                    block_id=index,
                    name=suggested_file.suggested_path,
                    source_language_hint=cast(str | None, original.metadata.get("source_language_hint")),
                    text=suggested_file.text,
                    context={
                        "source_kind": "textify_output",
                        "suggested_path": suggested_file.suggested_path,
                        "textify_output_source": record.output_source.to_json(),
                    },
                ).to_json()
                for index, suggested_file in enumerate(textify_response.source.suggested_files, start=1)
            ],
            "request_id": f"translate-{label}",
        }
    else:
        metadata = {
            "text": _text_from_already_text_candidate(original),
            "name": f"{label}_text",
            "source_language_hint": original.metadata.get("source_language_hint"),
            "context": {
                "source_kind": "download_text",
                "textify_output_source": record.output_source.to_json(),
            },
            "request_id": f"translate-{label}",
        }
    return ProcessCandidate(
        source_ref=record.output_source,
        imsgx=record.imsgx,
        source=original.source,
        artifact_key=_artifact_key_from_ref(record.output_source),
        metadata=metadata,
    )


def _text_from_already_text_candidate(candidate: ProcessCandidate) -> str:
    for key in ("evidence_text", "text"):
        value = candidate.metadata.get(key)
        if isinstance(value, str):
            return value
    raise AssertionError("already-text integration candidate must carry evidence_text or text")


def _artifact_key_from_ref(ref: ProcessRef) -> str | None:
    if ref.artifact_path is None:
        return None
    return Path(ref.artifact_path).name


def _translated_block(block: Block) -> TranslatedBlock:
    if "Bonjour" in block.text:
        return TranslatedBlock(
            block_id=block.block_id,
            name=block.name,
            detected_language="fr",
            english_confidence_estimate=0.01,
            translation_required=True,
            translated_text="Hello world. Curio is ready.",
        )
    return TranslatedBlock(
        block_id=block.block_id,
        name=block.name,
        detected_language="en",
        english_confidence_estimate=0.99,
        translation_required=False,
        translated_text=None,
    )


def records_by_source(records: tuple[ProcessRecord, ...], stage: PipelineStage) -> Mapping[str, ProcessRecord]:
    return {record.source_ref.source: record for record in records if record.stage == stage.value}


def object_payload(artifacts: InMemoryArtifactStore, record: ProcessRecord) -> JsonObject:
    assert record.object_ is not None
    assert record.object_.path is not None
    return cast(JsonObject, artifacts.objects[record.object_.path]["object"])


def test_offline_artifact_through_pipeline_uses_fake_stores_and_smoke_fixtures() -> None:
    image_case = smoke_case("R-IMG-TERMINAL-01")
    text_case = smoke_case("R-HTML-ARXIV-01")
    unsupported_case = smoke_case("R-ZIP-REPO-01")
    failure_case = smoke_case("R-IMG-DASH-01")
    textify_candidates = [
        download_candidate(label="image-needs-textify", case=image_case, row_number=57),
        download_candidate(
            label="non-english-text",
            case=text_case,
            row_number=74,
            evidence_text="Bonjour le monde. Curio est prêt.",
            source_language_hint="fr",
        ),
        download_candidate(
            label="english-text",
            case=text_case,
            row_number=75,
            evidence_text="Already English. Curio is ready.",
            source_language_hint="en",
        ),
        download_candidate(label="unsupported-media", case=unsupported_case, row_number=411),
        download_candidate(label="failed-provider", case=failure_case, row_number=109, force_textify_failure=True),
    ]
    artifacts = InMemoryArtifactStore()
    store = OfflineArtifactThroughStore(textify_candidates, artifacts)
    textify_service = OfflineTextifyService()
    translation_service = OfflineTranslationService()

    result = run_artifact_through(
        [TextifyProcessor(textify_service), TranslateProcessor(translation_service)],
        store=store,
        artifacts=artifacts,
        limit=10,
    )

    assert result.made_progress is True
    assert result.processor_results[-2].status == ProcessorRunStatus.NO_CANDIDATE
    assert result.processor_results[-1].status == ProcessorRunStatus.NO_CANDIDATE

    textify_records = records_by_source(store.records, PipelineStage.TEXTIFY)
    assert {record.status for record in textify_records.values()} == {
        TextifyProcessStatus.CONVERTED.value,
        TextifyProcessStatus.ALREADY_TEXT.value,
        TextifyProcessStatus.UNSUPPORTED.value,
        TextifyProcessStatus.FAILED.value,
    }
    assert textify_records["fixture://image-needs-textify"].object_ is not None
    assert textify_records["fixture://non-english-text"].object_ is None
    assert textify_records["fixture://english-text"].object_ is None
    assert textify_records["fixture://unsupported-media"].object_ is None
    assert textify_records["fixture://failed-provider"].object_ is None

    translate_records = records_by_source(store.records, PipelineStage.TRANSLATE)
    assert set(translate_records) == {
        "fixture://image-needs-textify",
        "fixture://non-english-text",
        "fixture://english-text",
    }
    assert translate_records["fixture://image-needs-textify"].status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert translate_records["fixture://non-english-text"].status == TranslateProcessStatus.TRANSLATED.value
    assert translate_records["fixture://english-text"].status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert translate_records["fixture://non-english-text"].object_ is not None
    assert translate_records["fixture://english-text"].object_ is None

    image_textify_record = textify_records["fixture://image-needs-textify"]
    image_translate_record = translate_records["fixture://image-needs-textify"]
    assert image_textify_record.output_source is not None
    assert image_translate_record.source_ref == image_textify_record.output_source
    assert image_translate_record.source_ref != textify_candidates[0].source_ref

    image_translate_request = next(
        request for request in translation_service.requests if request.request_id == "translate-image-needs-textify"
    )
    assert image_translate_request.blocks[0].text == image_case.ground_truth_text
    assert image_translate_request.blocks[0].context["textify_output_source"] == image_textify_record.output_source.to_json()

    non_english_payload = object_payload(artifacts, translate_records["fixture://non-english-text"])
    assert non_english_payload["blocks"][0]["translated_text"] == "Hello world. Curio is ready."

    image_payload = object_payload(artifacts, image_textify_record)
    assert image_payload["source"]["suggested_files"][0]["text"] == image_case.ground_truth_text
    assert all(not request.source.path.startswith("https://docs.google.com") for request in textify_service.requests)
