from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from curio.llm_caller import LlmUsage, ProviderName

JsonObject = dict[str, Any]
JsonValue = Any

TRANSLATION_REQUEST_VERSION = "curio-translation-request.v1"
TRANSLATION_RESPONSE_VERSION = "curio-translation-response.v1"
DEFAULT_TARGET_LANGUAGE = "en"
DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD = 0.90


class TranslationError(Exception):
    pass


class TranslationRequestError(TranslationError):
    pass


class TranslationResponseError(TranslationError):
    pass


class TranslationNotImplementedError(TranslationError):
    pass


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value


def _require_probability(value: object, field_name: str) -> float | int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number between 0 and 1")
    if not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be a number between 0 and 1")
    return value


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _coerce_warnings(values: Sequence[str]) -> tuple[str, ...]:
    warnings = tuple(values)
    for warning in warnings:
        _require_string(warning, "warning")
    if len(warnings) != len(set(warnings)):
        raise ValueError("warnings must be unique")
    return warnings


def counts_as_english(detected_language: str, english_confidence: float, threshold: float) -> bool:
    _require_string(detected_language, "detected_language")
    _require_probability(english_confidence, "english_confidence")
    _require_probability(threshold, "threshold")
    normalized_language = detected_language.casefold()
    return (normalized_language == "en" or normalized_language.startswith("en-")) and english_confidence >= threshold


@dataclass(frozen=True, slots=True)
class Block:
    block_id: int
    name: str
    source_language_hint: str | None
    text: str
    context: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_positive_int(self.block_id, "block_id")
        _require_string(self.name, "name")
        if self.source_language_hint is not None:
            _require_string(self.source_language_hint, "source_language_hint")
        _require_string(self.text, "text")
        object.__setattr__(self, "context", dict(_require_mapping(self.context, "context")))

    def to_json(self) -> JsonObject:
        return {
            "block_id": self.block_id,
            "name": self.name,
            "source_language_hint": self.source_language_hint,
            "text": self.text,
            "context": dict(self.context),
        }


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    request_id: str
    blocks: Sequence[Block]
    target_language: str = DEFAULT_TARGET_LANGUAGE
    english_confidence_threshold: float = DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD
    provider: ProviderName | str | None = None
    model: str | None = None
    timeout_seconds: int | None = None
    translation_request_version: str = field(default=TRANSLATION_REQUEST_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        if self.target_language != DEFAULT_TARGET_LANGUAGE:
            raise TranslationRequestError("target_language must be en")
        _require_probability(self.english_confidence_threshold, "english_confidence_threshold")
        blocks = tuple(self.blocks)
        if not blocks:
            raise TranslationRequestError("blocks must not be empty")
        block_ids = tuple(block.block_id for block in blocks)
        if len(block_ids) != len(set(block_ids)):
            raise TranslationRequestError("block_id values must be unique")
        if self.provider is not None:
            object.__setattr__(self, "provider", ProviderName(self.provider))
        if self.model is not None:
            _require_string(self.model, "model")
        if self.timeout_seconds is not None:
            _require_positive_int(self.timeout_seconds, "timeout_seconds")
        object.__setattr__(self, "blocks", blocks)

    def to_json(self) -> JsonObject:
        provider = None if self.provider is None else cast(ProviderName, self.provider)
        return {
            "translation_request_version": self.translation_request_version,
            "request_id": self.request_id,
            "target_language": self.target_language,
            "english_confidence_threshold": self.english_confidence_threshold,
            "blocks": [block.to_json() for block in self.blocks],
            "provider": None if provider is None else provider.value,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True, slots=True)
class TranslatedBlock:
    block_id: int
    name: str
    detected_language: str
    english_confidence_estimate: float
    translation_required: bool
    translated_text: str | None
    warnings: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_positive_int(self.block_id, "block_id")
        _require_string(self.name, "name")
        _require_string(self.detected_language, "detected_language")
        _require_probability(self.english_confidence_estimate, "english_confidence_estimate")
        if self.translation_required and self.translated_text is None:
            raise TranslationResponseError("translated_text is required when translation_required is true")
        if not self.translation_required and self.translated_text is not None:
            raise TranslationResponseError("translated_text must be null when translation_required is false")
        if self.translated_text is not None:
            _require_string(self.translated_text, "translated_text")
        object.__setattr__(self, "warnings", _coerce_warnings(self.warnings))

    def to_json(self) -> JsonObject:
        return {
            "block_id": self.block_id,
            "name": self.name,
            "detected_language": self.detected_language,
            "english_confidence_estimate": self.english_confidence_estimate,
            "translation_required": self.translation_required,
            "translated_text": self.translated_text,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class LlmSummary:
    provider: ProviderName | str
    model: str | None
    usage: LlmUsage

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", ProviderName(self.provider))
        if self.model is not None:
            _require_string(self.model, "model")

    def to_json(self) -> JsonObject:
        provider = cast(ProviderName, self.provider)
        return {
            "provider": provider.value,
            "model": self.model,
            "usage": self.usage.to_json(),
        }


@dataclass(frozen=True, slots=True)
class TranslationResponse:
    request_id: str
    blocks: Sequence[TranslatedBlock]
    llm: LlmSummary
    target_language: str = DEFAULT_TARGET_LANGUAGE
    warnings: Sequence[str] = field(default_factory=tuple)
    translation_response_version: str = field(default=TRANSLATION_RESPONSE_VERSION, init=False)

    def __post_init__(self) -> None:
        _require_string(self.request_id, "request_id")
        if self.target_language != DEFAULT_TARGET_LANGUAGE:
            raise TranslationResponseError("target_language must be en")
        blocks = tuple(self.blocks)
        if not blocks:
            raise TranslationResponseError("blocks must not be empty")
        object.__setattr__(self, "blocks", blocks)
        object.__setattr__(self, "warnings", _coerce_warnings(self.warnings))

    def to_json(self) -> JsonObject:
        return {
            "translation_response_version": self.translation_response_version,
            "request_id": self.request_id,
            "target_language": self.target_language,
            "blocks": [block.to_json() for block in self.blocks],
            "llm": self.llm.to_json(),
            "warnings": list(self.warnings),
        }
