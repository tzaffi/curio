from collections.abc import Mapping, Sequence
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError

from curio.llm_caller import LlmResponse, LlmStatus
from curio.translate.adapter import translation_model_output_schema
from curio.translate.models import (
    JsonValue,
    TranslatedBlock,
    TranslationRequest,
    TranslationResponseError,
    counts_as_english,
)


def translated_blocks_from_llm_response(
    request: TranslationRequest,
    response: LlmResponse,
) -> tuple[TranslatedBlock, ...]:
    if response.request_id != request.request_id:
        raise TranslationResponseError("LLM response request_id must match translation request_id")
    if response.status != LlmStatus.SUCCEEDED:
        raise TranslationResponseError("LLM response status must be succeeded")
    if response.output is None:
        raise TranslationResponseError("LLM response output is required")

    validate_translation_model_output(response.output.value)
    payload = _require_mapping(response.output.value, "LLM output value")
    output_request_id = _require_string(_require_field(payload, "request_id"), "request_id")
    if output_request_id != request.request_id:
        raise TranslationResponseError("LLM output request_id must match translation request_id")

    blocks = tuple(
        TranslatedBlock.from_json(block)
        for block in _require_list(_require_field(payload, "blocks"), "blocks")
    )
    validate_translated_blocks(request, blocks)
    return blocks


def validate_translation_model_output(value: JsonValue) -> None:
    validator = Draft202012Validator(
        translation_model_output_schema(),
        format_checker=FormatChecker(),
    )
    try:
        validator.validate(value)
    except JsonSchemaLibraryError as exc:
        raise TranslationResponseError(f"LLM output failed translation schema validation: {exc.message}") from exc


def validate_translated_blocks(
    request: TranslationRequest,
    blocks: Sequence[TranslatedBlock],
) -> None:
    input_ids = tuple(block.block_id for block in request.blocks)
    output_ids = tuple(block.block_id for block in blocks)

    duplicated_ids = _duplicated_ids(output_ids)
    if duplicated_ids:
        raise TranslationResponseError(f"duplicate translated block ids: {_format_ids(duplicated_ids)}")

    missing_ids = tuple(block_id for block_id in input_ids if block_id not in output_ids)
    if missing_ids:
        raise TranslationResponseError(f"missing translated block ids: {_format_ids(missing_ids)}")

    extra_ids = tuple(block_id for block_id in output_ids if block_id not in input_ids)
    if extra_ids:
        raise TranslationResponseError(f"unexpected translated block ids: {_format_ids(extra_ids)}")

    if output_ids != input_ids:
        raise TranslationResponseError("translated block order must match input block order")

    input_by_id = {block.block_id: block for block in request.blocks}
    for block in blocks:
        input_block = input_by_id[block.block_id]
        if block.name != input_block.name:
            raise TranslationResponseError(f"translated block name must match input block name for block_id {block.block_id}")
        block_counts_as_english = counts_as_english(
            block.detected_language,
            block.english_confidence_estimate,
            request.english_confidence_threshold,
        )
        if block_counts_as_english and block.translation_required:
            raise TranslationResponseError(
                f"block_id {block.block_id} counts as English and must not require translation"
            )
        if not block_counts_as_english and not block.translation_required:
            raise TranslationResponseError(f"block_id {block.block_id} must require translation")


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise TranslationResponseError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _require_list(value: object, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise TranslationResponseError(f"{field_name} must be a list")
    return cast(list[object], value)


def _require_field(payload: Mapping[str, JsonValue], field_name: str) -> JsonValue:
    if field_name not in payload:
        raise TranslationResponseError(f"{field_name} is required")
    return payload[field_name]


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TranslationResponseError(f"{field_name} must be a string")
    if not value.strip():
        raise TranslationResponseError(f"{field_name} must not be empty")
    return value


def _duplicated_ids(block_ids: Sequence[int]) -> tuple[int, ...]:
    seen: set[int] = set()
    duplicates: list[int] = []
    for block_id in block_ids:
        if block_id in seen and block_id not in duplicates:
            duplicates.append(block_id)
        seen.add(block_id)
    return tuple(duplicates)


def _format_ids(block_ids: Sequence[int]) -> str:
    return ", ".join(str(block_id) for block_id in block_ids)
