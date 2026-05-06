import hashlib
import json
import re
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
    normalize_mime_type,
)
from curio.translate import (
    DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD,
    DEFAULT_TARGET_LANGUAGE,
    Block,
    TranslationRequest,
    TranslationResponse,
    normalize_language_hint,
)

TEXTIFY_PROCESSOR_VERSION = "curio-textify-processor.v1"
TRANSLATE_PROCESSOR_VERSION = "curio-translate-processor.v1"
UNSUPPORTED_TEXTIFY_VIDEO_EXTENSIONS = frozenset((".3gp", ".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"))
URL_RE = re.compile(r"(?:https?://|www\.|t\.co/|pic\.x\.com/)\S+", re.IGNORECASE)


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
        unsupported_reason = _known_unsupported_textify_reason(candidate)
        if unsupported_reason is not None:
            return Eligibility(
                eligible=False,
                status=TextifyProcessStatus.UNSUPPORTED.value,
                metadata={
                    "textify_status": TextifyStatus.UNSUPPORTED_MEDIA.value,
                    "warnings": [unsupported_reason],
                },
            )
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
        request = _translation_request_from_candidate(candidate)
        if _deterministically_already_english(request):
            return Eligibility(
                eligible=False,
                status=TranslateProcessStatus.ALREADY_ENGLISH.value,
                metadata={
                    "translated_blocks": 0,
                    "warnings": ["translation skipped because candidate text is already English or URL-only"],
                },
            )
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
        raise ValueError(_missing_textify_path_message(candidate))
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


def _known_unsupported_textify_reason(candidate: ProcessCandidate) -> str | None:
    metadata = candidate.metadata
    mime_type = _metadata_string(metadata, "mime_type")
    if mime_type is not None and (normalize_mime_type(mime_type) or "").startswith("video/"):
        return "unsupported media type for textify v1: video"
    for field_name in ("type", "column"):
        value = _metadata_string(metadata, field_name)
        normalized_value = "" if value is None else _compact_media_value(value)
        if normalized_value == "video":
            return "unsupported media type for textify v1: video"
        if normalized_value == "animatedgif":
            return "unsupported media type for textify v1: animated gif"
    if any(_looks_like_video_resource(value) for value in _candidate_textify_identity_values(candidate)):
        return "unsupported media type for textify v1: video"
    return None


def _compact_media_value(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _candidate_textify_identity_values(candidate: ProcessCandidate) -> tuple[str, ...]:
    metadata = candidate.metadata
    values = [
        candidate.source,
        candidate.artifact_key,
        candidate.source_ref.source,
        candidate.source_ref.artifact_url,
        candidate.source_ref.artifact_path,
    ]
    for field_name in ("source", "object", "path", "name"):
        value = _metadata_string(metadata, field_name)
        if value is not None:
            values.append(value)
    return tuple(value for value in values if value)


def _looks_like_video_resource(value: str) -> bool:
    normalized = value.strip().casefold()
    resource = normalized.split("?", 1)[0].split("#", 1)[0]
    return "/video/" in resource or any(resource.endswith(extension) for extension in UNSUPPORTED_TEXTIFY_VIDEO_EXTENSIONS)


def _missing_textify_path_message(candidate: ProcessCandidate) -> str:
    detail_fields = (
        ("downloads_dir", candidate.metadata.get("downloads_dir")),
        ("expected_artifact_prefix", candidate.metadata.get("expected_artifact_prefix")),
        ("downloads_row", candidate.metadata.get("downloads_row", candidate.source_ref.row_number)),
        ("column", candidate.metadata.get("column")),
        ("type", candidate.metadata.get("type")),
        ("object", candidate.metadata.get("object")),
    )
    details = ", ".join(
        f"{name}={value}" for name, value in detail_fields if value is not None and str(value).strip()
    )
    base = "textify candidate metadata requires path or source_ref.artifact_path"
    return base if not details else f"{base} ({details})"


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


def _deterministically_already_english(request: TranslationRequest) -> bool:
    return all(_block_is_deterministically_already_english(block) for block in request.blocks)


def _block_is_deterministically_already_english(block: Block) -> bool:
    if _is_url_only_text(block.text):
        return True
    source_language_hint = normalize_language_hint(block.source_language_hint)
    if source_language_hint is None:
        return False
    if source_language_hint != "en" and not source_language_hint.startswith("en-"):
        return False
    return not _has_substantial_non_latin_text(block.text)


def _is_url_only_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return not URL_RE.sub("", stripped).strip()


def _has_substantial_non_latin_text(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    non_latin_letters = [char for char in letters if not ("a" <= char.casefold() <= "z")]
    return len(non_latin_letters) >= 3 and len(non_latin_letters) / len(letters) > 0.10


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
