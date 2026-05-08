from pathlib import Path

import pytest

import curio.pipeline as pipeline
import curio.pipeline.processors as processors_module
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
from curio.pipeline.local import LocalArtifactStore
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


def make_candidate_without_artifact(metadata: dict[str, object], *, source: str = "x://post/123") -> ProcessCandidate:
    source_ref = ProcessRef(
        stage="download",
        tab="downloads",
        source=source,
        row_number=1,
    )
    return ProcessCandidate(
        source_ref=source_ref,
        imsgx=source_ref,
        source=source,
        artifact_key=None,
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


class FailingTranslationService:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def translate(self, request: object) -> TranslationResponse:
        self.requests.append(request)
        raise RuntimeError("catastrophic translate failure")


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


def test_textify_processor_records_known_unsupported_video_without_artifact_or_service_call() -> None:
    candidate = make_candidate_without_artifact(
        {
            "source": "https://x.com/sharbel/status/2025944354070659094/video/1",
            "type": "Tweet",
            "column": "Text",
            "object": "https://drive.google.com/file/d/video-file/view",
        },
        source="https://x.com/sharbel/status/2025944354070659094/video/1",
    )
    service = FakeTextifyService(make_textify_response(TextifyStatus.CONVERTED))
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})
    artifacts = InMemoryArtifactStore()

    result = run_processor_once(TextifyProcessor(service), store=store, artifacts=artifacts)

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.UNSUPPORTED.value
    assert result.record.object_ is None
    assert result.record.metadata == {
        "textify_status": TextifyStatus.UNSUPPORTED_MEDIA.value,
        "warnings": ["unsupported media type for textify v1: video"],
    }
    assert service.requests == []
    assert artifacts.objects == {}


@pytest.mark.parametrize(
    "metadata",
    [
        {"mime_type": "video/mp4"},
        {"type": "Video"},
        {"column": "Video"},
        {"type": "AnimatedGif"},
        {"name": "clip.mov"},
        {"object": "https://example.com/media/clip.webm?download=1"},
    ],
)
def test_textify_processor_known_unsupported_video_classifiers_skip_before_request(metadata: dict[str, object]) -> None:
    candidate = make_candidate_without_artifact(metadata)
    service = FakeTextifyService(make_textify_response(TextifyStatus.CONVERTED))
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})

    result = run_processor_once(TextifyProcessor(service), store=store, artifacts=InMemoryArtifactStore())

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.UNSUPPORTED.value
    assert service.requests == []


def test_textify_processor_records_missing_link_artifact_as_already_text() -> None:
    candidate = make_candidate_without_artifact(
        {
            "downloads_dir": "/tmp/downloads",
            "expected_artifact_prefix": "imsgx-r0574-x3-link-",
            "downloads_row": 1107,
            "column": "X3",
            "type": "Link",
            "object": "https://www.skool.com/ai-profit-lab-7462/about",
        },
        source="https://www.skool.com/ai-profit-lab-7462/about",
    )
    service = FakeTextifyService(make_textify_response(TextifyStatus.CONVERTED))
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})

    result = run_processor_once(TextifyProcessor(service), store=store, artifacts=InMemoryArtifactStore())

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.ALREADY_TEXT.value
    assert result.record.object_ is None
    assert result.record.output_source == candidate.source_ref
    assert result.record.metadata == {
        "textify_status": TextifyStatus.SKIPPED_TEXT_MEDIA.value,
        "warnings": ["link has no downloaded artifact for textify; using URL as text"],
    }
    assert service.requests == []


def test_textify_processor_requires_path() -> None:
    source_ref = ProcessRef(stage="download", tab="downloads", source="x://post/123")
    candidate = ProcessCandidate(
        source_ref=source_ref,
        imsgx=source_ref,
        source="x://post/123",
        metadata={
            "downloads_dir": "/tmp/downloads",
            "expected_artifact_prefix": "imsgx-r0008-x1-image-",
            "downloads_row": 25,
            "column": "X1",
            "type": "Image",
            "object": "https://drive/object",
        },
    )
    store = InMemoryPipelineStore({PipelineStage.TEXTIFY.value: [candidate]})

    result = run_processor_once(
        TextifyProcessor(FakeTextifyService(make_textify_response(TextifyStatus.CONVERTED))),
        store=store,
        artifacts=InMemoryArtifactStore(),
    )

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.FAILED.value
    assert result.record.metadata["error"].startswith("textify candidate metadata requires path or source_ref.artifact_path")
    assert "downloads_dir=/tmp/downloads" in result.record.metadata["error"]
    assert "expected_artifact_prefix=imsgx-r0008-x1-image-" in result.record.metadata["error"]
    assert "downloads_row=25" in result.record.metadata["error"]
    assert "column=X1" in result.record.metadata["error"]
    assert "type=Image" in result.record.metadata["error"]
    assert "object=https://drive/object" in result.record.metadata["error"]


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
    artifacts = InMemoryArtifactStore()

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=artifacts)

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert result.record.object_ is None
    assert result.record.output_source == candidate.source_ref
    assert artifacts.objects == {}
    assert service.requests[0].blocks[0].text == "Already English."


def test_translate_processor_skips_clearly_english_text_without_provider_or_artifact(tmp_path: Path) -> None:
    candidate = make_candidate(
        {
            "text": "Nous officially cooked with Hermes Agent. First time using a local-model agent.",
            "name": "tweet",
            "source_language_hint": "English",
        }
    )
    service = FakeTranslationService(
        make_translation_response(
            TranslatedBlock(
                block_id=1,
                name="tweet",
                detected_language="en",
                english_confidence_estimate=0.99,
                translation_required=False,
                translated_text=None,
            )
        )
    )
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=LocalArtifactStore(tmp_path))

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert result.record.object_ is None
    assert result.record.output_source == candidate.source_ref
    assert result.record.metadata == {
        "translated_blocks": 0,
        "warnings": ["translation skipped because candidate text is already English or URL-only"],
    }
    assert service.requests == []
    assert not (tmp_path / "translations").exists()


def test_translate_processor_skips_url_only_text_without_provider_or_artifact(tmp_path: Path) -> None:
    candidate = make_candidate({"text": "https://t.co/f4BOUjXmF8", "name": "tweet"})
    service = FakeTranslationService(
        make_translation_response(
            TranslatedBlock(
                block_id=1,
                name="tweet",
                detected_language="zxx",
                english_confidence_estimate=0,
                translation_required=True,
                translated_text="https://t.co/f4BOUjXmF8",
            )
        )
    )
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=LocalArtifactStore(tmp_path))

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert result.record.object_ is None
    assert service.requests == []
    assert not (tmp_path / "translations").exists()


def test_translation_url_only_helper_ignores_blank_text() -> None:
    assert processors_module._is_url_only_text(" ") is False


def test_translate_processor_skips_non_language_identifier_with_english_hint(tmp_path: Path) -> None:
    candidate = make_candidate({"text": "12345", "name": "tweet", "source_language_hint": "en"})
    service = FakeTranslationService(
        make_translation_response(
            TranslatedBlock(
                block_id=1,
                name="tweet",
                detected_language="en",
                english_confidence_estimate=0.99,
                translation_required=False,
                translated_text=None,
            )
        )
    )
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=LocalArtifactStore(tmp_path))

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert service.requests == []


def test_translate_processor_already_english_creates_no_local_artifact(tmp_path: Path) -> None:
    candidate = make_candidate({"text": "Already English.", "name": "note"})
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

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=LocalArtifactStore(tmp_path))

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert result.record.object_ is None
    assert not (tmp_path / "translations").exists()


def test_translate_processor_service_failure_records_failed_without_artifact(tmp_path: Path) -> None:
    candidate = make_candidate({"text": "bonjour", "name": "note"})
    service = FailingTranslationService()
    store = InMemoryPipelineStore({PipelineStage.TRANSLATE.value: [candidate]})

    result = run_processor_once(TranslateProcessor(service), store=store, artifacts=LocalArtifactStore(tmp_path))

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.FAILED.value
    assert result.record.object_ is None
    assert result.record.metadata["error"] == "catastrophic translate failure"
    assert not (tmp_path / "translations").exists()


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
    artifacts = InMemoryArtifactStore()

    result = run_processor_once(
        TranslateProcessor(FakeTranslationService(make_translation_response(block))),
        store=store,
        artifacts=artifacts,
    )

    assert result.record is not None
    assert result.record.status == TranslateProcessStatus.FAILED.value
    assert result.record.object_ is None
    assert expected_error in result.record.metadata["error"]
    assert artifacts.objects == {}
