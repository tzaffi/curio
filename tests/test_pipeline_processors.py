from pathlib import Path

import pytest

import curio.pipeline as pipeline
from curio.llm_caller import LlmUsage
from curio.pipeline import (
    InMemoryArtifactStore,
    InMemoryPipelineStore,
    PipelineStage,
    ProcessCandidate,
    ProcessRef,
    TextifyProcessor,
    TextifyProcessStatus,
    TranslateProcessor,
    TranslateProcessStatus,
    run_processor_once,
)
from curio.textify import (
    SuggestedTextFile,
    TextifiedSource,
    TextifyResponse,
    TextifyStatus,
)
from curio.translate import Block, LlmSummary, TranslatedBlock, TranslationResponse


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


def make_candidate(metadata: dict[str, object], *, source: str = "x://post/123") -> ProcessCandidate:
    source_ref = ProcessRef(
        stage="download",
        tab="downloads",
        source=source,
        row_number=1,
        artifact_path="/tmp/source.txt",
        artifact_sha256="abc123",
    )
    return ProcessCandidate(
        source_ref=source_ref,
        imsgx=source_ref,
        source=source,
        artifact_key="source.txt",
        metadata=metadata,
    )


def make_textify_response(status: TextifyStatus, *, request_id: str = "textify-test") -> TextifyResponse:
    suggested_files = (
        [
            SuggestedTextFile(
                suggested_path="source.md",
                output_format="markdown",
                text="# Hello",
            )
        ]
        if status == TextifyStatus.CONVERTED
        else []
    )
    return TextifyResponse(
        request_id=request_id,
        source=TextifiedSource(
            name="source.png",
            input_mime_type="image/png",
            source_sha256="abc123",
            textification_required=status != TextifyStatus.SKIPPED_TEXT_MEDIA,
            status=status,
            suggested_files=suggested_files,
            warnings=["source warning"],
        ),
        warnings=["request warning"],
    )


class FakeTextifyService:
    def __init__(self, response: TextifyResponse) -> None:
        self.response = response
        self.requests: list[object] = []

    def textify(self, request: object) -> TextifyResponse:
        self.requests.append(request)
        return self.response


def make_translation_response(
    block: TranslatedBlock,
    *,
    request_id: str = "translate-test",
) -> TranslationResponse:
    return TranslationResponse(
        request_id=request_id,
        blocks=[block],
        llm=LlmSummary(provider="codex_cli", model="gpt-test", usage=make_usage()),
        warnings=["request warning"],
    )


class FakeTranslationService:
    def __init__(self, response: TranslationResponse) -> None:
        self.response = response
        self.requests: list[object] = []

    def translate(self, request: object) -> TranslationResponse:
        self.requests.append(request)
        return self.response


def test_pipeline_root_exports_processors() -> None:
    assert "TextifyProcessor" in pipeline.__all__
    assert "TranslateProcessor" in pipeline.__all__
    assert "TEXTIFY_PROCESSOR_VERSION" in pipeline.__all__
    assert "TRANSLATE_PROCESSOR_VERSION" in pipeline.__all__


def test_textify_processor_converts_and_persists_response(tmp_path: Path) -> None:
    artifact = tmp_path / "scan.png"
    artifact.write_bytes(b"png")
    candidate = make_candidate(
        {
            "path": str(artifact),
            "name": "scan.png",
            "mime_type": "image/png",
            "source_language_hint": "ja",
            "request_id": "textify-custom",
            "llm_caller": "textifier",
        }
    )
    service = FakeTextifyService(make_textify_response(TextifyStatus.CONVERTED, request_id="textify-custom"))
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})
    artifacts = InMemoryArtifactStore()

    result = run_processor_once(TextifyProcessor(service), store=store, artifacts=artifacts)

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.CONVERTED.value
    assert result.record.object_ is not None
    assert result.record.output_source is not None
    assert result.record.output_source.artifact_path == result.record.object_.path
    assert result.record.metadata == {
        "request_id": "textify-custom",
        "textify_status": TextifyStatus.CONVERTED.value,
        "warnings": ["request warning", "source warning"],
    }
    request = service.requests[0]
    assert request.request_id == "textify-custom"
    assert request.llm_caller == "textifier"
    assert request.source.source_language_hint == "ja"


@pytest.mark.parametrize(
    ("textify_status", "process_status", "expected_output_source"),
    [
        (TextifyStatus.SKIPPED_TEXT_MEDIA, TextifyProcessStatus.ALREADY_TEXT.value, True),
        (TextifyStatus.UNSUPPORTED_MEDIA, TextifyProcessStatus.UNSUPPORTED.value, False),
        (TextifyStatus.NO_TEXT_FOUND, TextifyProcessStatus.NO_TEXT.value, False),
    ],
)
def test_textify_processor_records_non_object_outcomes(
    textify_status: TextifyStatus,
    process_status: str,
    expected_output_source: bool,
) -> None:
    candidate = make_candidate(
        {
            "evidence_text": "already text",
            "context": {"artifact_kind": "tweet_json"},
        }
    )
    service = FakeTextifyService(make_textify_response(textify_status))
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})

    result = run_processor_once(TextifyProcessor(service), store=store, artifacts=InMemoryArtifactStore())

    assert result.record is not None
    assert result.record.status == process_status
    assert result.record.object_ is None
    assert (result.record.output_source == candidate.source_ref) is expected_output_source
    assert service.requests[0].source.context == {
        "artifact_kind": "tweet_json",
        "evidence_text": "already text",
    }


def test_textify_processor_requires_path() -> None:
    source_ref = ProcessRef(stage="download", tab="downloads", source="x://post/123")
    candidate = ProcessCandidate(source_ref=source_ref, imsgx=source_ref, source="x://post/123")
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})

    result = run_processor_once(
        TextifyProcessor(FakeTextifyService(make_textify_response(TextifyStatus.CONVERTED))),
        store=store,
        artifacts=InMemoryArtifactStore(),
    )

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.FAILED.value
    assert result.record.metadata["error"] == "textify candidate metadata requires path or source_ref.artifact_path"


def test_translate_processor_translates_text_and_persists_response() -> None:
    candidate = make_candidate(
        {
            "text": "今日は新しいモデルを公開します。",
            "name": "tweet_text",
            "source_language_hint": "ja",
            "context": {"artifact_kind": "tweet_json"},
            "english_confidence_threshold": 0.5,
            "request_id": "translate-custom",
            "llm_caller": "translator",
        }
    )
    block = TranslatedBlock(
        block_id=1,
        name="tweet_text",
        detected_language="ja",
        english_confidence_estimate=0.01,
        translation_required=True,
        translated_text="Today we are releasing a new model.",
        warnings=["block warning"],
    )
    service = FakeTranslationService(make_translation_response(block, request_id="translate-custom"))
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=InMemoryArtifactStore())

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.TRANSLATED.value
    assert result.record.object_ is not None
    assert result.record.output_source is not None
    assert result.record.metadata == {
        "request_id": "translate-custom",
        "translated_blocks": 1,
        "warnings": ["request warning", "block warning"],
    }
    request = service.requests[0]
    assert request.request_id == "translate-custom"
    assert request.english_confidence_threshold == 0.5
    assert request.llm_caller == "translator"
    assert request.blocks[0] == Block(
        block_id=1,
        name="tweet_text",
        source_language_hint="ja",
        text="今日は新しいモデルを公開します。",
        context={"artifact_kind": "tweet_json"},
    )


def test_translate_processor_uses_structured_blocks_and_records_already_english() -> None:
    candidate = make_candidate(
        {
            "blocks": [
                Block(
                    block_id=1,
                    name="note",
                    source_language_hint=None,
                    text="Already English.",
                ).to_json()
            ],
        }
    )
    block = TranslatedBlock(
        block_id=1,
        name="note",
        detected_language="en",
        english_confidence_estimate=0.99,
        translation_required=False,
        translated_text=None,
    )
    service = FakeTranslationService(make_translation_response(block))
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=InMemoryArtifactStore())

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert result.record.object_ is None
    assert result.record.output_source == candidate.source_ref
    assert service.requests[0].blocks[0].text == "Already English."


@pytest.mark.parametrize(
    ("metadata", "expected_error"),
    [
        ({}, "translation candidate metadata requires blocks or text"),
        ({"blocks": "not-blocks"}, "translation candidate blocks must be a sequence"),
        ({"text": "hello", "english_confidence_threshold": True}, "english_confidence_threshold must be a number"),
        ({"text": "hello", "context": []}, "context must be an object"),
        ({"text": 1}, "text must be a string"),
    ],
)
def test_translate_processor_records_invalid_candidate_failures(
    metadata: dict[str, object],
    expected_error: str,
) -> None:
    candidate = make_candidate(metadata)
    block = TranslatedBlock(
        block_id=1,
        name="note",
        detected_language="en",
        english_confidence_estimate=0.99,
        translation_required=False,
        translated_text=None,
    )
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(
        TranslateProcessor(FakeTranslationService(make_translation_response(block))),
        store=store,
        artifacts=InMemoryArtifactStore(),
    )

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.FAILED.value
    assert expected_error in result.record.metadata["error"]
