# Curio Translation

## Purpose

Define the normative v1 translation behavior used by Curio as a standalone command, reusable Python module, and dossier-preparation step.

This document is normative for:

- when Curio decides a text block needs translation
- how English is defined for translation purposes
- the standalone translation JSON request and response contract
- the module boundary for reusable translation
- how translation uses `curio.llm_caller`
- where translated text is stored in persisted evaluation payloads
- how translated blocks relate to original `dossier_snapshot.evidence_text` blocks
- how translated and non-translated blocks are identified

The machine-readable counterparts to this document are:

- [schemas/translation_request.schema.json](schemas/translation_request.schema.json)
- [schemas/translation_response.schema.json](schemas/translation_response.schema.json)

This document is not the place to define:

- the Google Sheets workbook model
- the detailed evaluation payload contract outside translation behavior
- provider adapter behavior
- external provider pricing
- downstream evaluation policy

Those belong in [SCHEMA.md](SCHEMA.md), [JSON-PAYLOAD.md](JSON-PAYLOAD.md), [LLM-CALLER.md](LLM-CALLER.md), and prompt files.

## Design Principles

The v1 translation workflow should follow these rules:

- Translation is a first-class Curio capability, not just an implementation detail of evaluation.
- Translation target is always English in v1.
- Translation operates per human-readable text block.
- Original text remains preserved when translation occurs.
- Translation must preserve meaning, not summarize or classify.
- Curio translates the full normalized source block before any dossier-size truncation.
- Translated English text belongs in `dossier_snapshot.evidence_text` because it is evaluator input.
- Translation does not belong in `evaluation`.
- Translation depends on `curio.llm_caller` for LLM execution.
- Translation code should be provider-neutral and testable with a fake `LlmClient`.
- `dossier_snapshot.evidence_text` remains an ordered list, not a keyed object.

## Module Boundary

The implementation module should be named:

```text
curio.translate
```

The public boundary should include:

- `TranslationService`
  A small service that accepts a translation request and an injected `LlmClient`.
- `TranslationRequest`
  Frozen slotted dataclass matching the JSON request shape.
- `TranslationResponse`
  Frozen slotted dataclass matching the JSON response shape.
- `Block`
  One source text block to detect and possibly translate.
- `TranslatedBlock`
  One detected and possibly translated text block result.

The command-line layer should only parse arguments, load config, call the service, and render output.

## Human-Readable Text Blocks

For dossier preparation, a human-readable text block is an `evidence_text` entry intended for semantic evaluation.

This includes blocks such as:

- `tweet_text`
- `page_main_text`
- `repo_readme`

This does not include metadata-only values stored in `dossier_snapshot.details`.

## Standalone Request Shape

The stable JSON representation of a translation request is:

```json
{
  "translation_request_version": "curio-translation-request.v1",
  "request_id": "translate-20260424-000001",
  "target_language": "en",
  "english_confidence_threshold": 0.9,
  "blocks": [
    {
      "block_id": 1,
      "name": "tweet_text",
      "source_language_hint": null,
      "text": "今日は新しいモデルを公開します。",
      "context": {
        "artifact_kind": "tweet_json"
      }
    }
  ],
  "provider": "codex_cli",
  "model": null,
  "timeout_seconds": 300
}
```

Fields:

- `translation_request_version`
  Fixed v1 request contract identifier. In v1 this must be `curio-translation-request.v1`.
- `request_id`
  Operator-visible identifier for logs and diagnostics.
- `target_language`
  Target language. V1 accepts only the exact value `en`. More specific English tags such as `en-US` or `en-GB` are not valid targets in v1, though they may appear as source or detected language values.
- `english_confidence_threshold`
  Minimum model confidence for treating a block as English without translation. V1 defaults to `0.90`.
- `blocks`
  Ordered source text blocks to detect and possibly translate.
- `provider`
  Optional provider override passed to `curio.llm_caller`.
- `model`
  Optional model override passed to `curio.llm_caller`.
- `timeout_seconds`
  Optional provider-call wall-clock timeout.

Each `blocks` item contains:

- `block_id`
  Positive integer unique within the request.
- `name`
  Stable block name such as `tweet_text`.
- `source_language_hint`
  Optional language hint from upstream extraction.
- `text`
  Full source text to inspect and translate.
- `context`
  Small optional diagnostic object. It must not contain large duplicate text.

## Standalone Response Shape

The stable JSON representation of a translation response is:

```json
{
  "translation_response_version": "curio-translation-response.v1",
  "request_id": "translate-20260424-000001",
  "target_language": "en",
  "blocks": [
    {
      "block_id": 1,
      "name": "tweet_text",
      "detected_language": "ja",
      "english_confidence_estimate": 0.01,
      "translation_required": true,
      "translated_text": "Today we are releasing a new model.",
      "warnings": []
    }
  ],
  "llm": {
    "provider": "codex_cli",
    "model": "gpt-5.3-codex",
    "usage": {
      "input_tokens": 800,
      "cached_input_tokens": null,
      "output_tokens": 80,
      "reasoning_tokens": null,
      "total_tokens": 880,
      "metered_objects": [],
      "started_at": "2026-04-24T15:20:00Z",
      "completed_at": "2026-04-24T15:20:03Z",
      "wall_seconds": 3.0,
      "thinking_seconds": null
    }
  },
  "warnings": []
}
```

Fields:

- `translation_response_version`
  Fixed v1 response contract identifier. In v1 this must be `curio-translation-response.v1`.
- `request_id`
  The request identifier from the input.
- `target_language`
  The accepted target language. In v1 this is always exactly `en`.
- `blocks`
  Ordered block results corresponding exactly to request blocks.
- `llm`
  Provider, model, and usage metadata from the underlying `LlmResponse`.
- `warnings`
  Compact request-level operational warnings.

Each block result contains:

- `block_id`
  The input block id.
- `name`
  The input block name.
- `detected_language`
  Language code detected for the source text.
- `english_confidence_estimate`
  Model-reported heuristic estimate that the source text is already English, as a float from `0.0` to `1.0`. This is not calibrated provider telemetry.
- `translation_required`
  Whether Curio translated the block.
- `translated_text`
  English translation when `translation_required` is true; otherwise `null`.
- `warnings`
  Compact block-level warnings.

## English Classification

Curio must perform language detection on each human-readable text block before evaluation.

A block counts as English only when all of the following are true:

- the detected language code is `en` or starts with `en-`
- the model's English confidence is at least the configured threshold

All other blocks must be translated to English before evaluation, including:

- non-English blocks
- mixed-language blocks
- ambiguous blocks below the confidence threshold

For standalone translation, English blocks are still reported in the response, but `translation_required` is false and `translated_text` is `null`.

Low English confidence must not abort translation and is not itself a warning. If the model cannot classify a block as English above the configured threshold, it must translate the block into English.

## English Confidence Policy

V1 uses model-reported English confidence estimates as a heuristic for deciding whether to translate.

The default policy is:

- `default_english_confidence_threshold = 0.90`
- unknown providers and models use the default threshold and the default prompt rubric
- provider/model-specific overrides may change the threshold and prompt rubric while preserving the same public response shape
- the resolved threshold is included in each `TranslationRequest` for reproducibility
- `english_confidence_estimate` is produced by the model according to the resolved rubric

Model-specific confidence behavior belongs in Curio configuration and prompt policy. It should not add extra public request fields beyond the resolved threshold used for the run.

## V1 Prompt Template

V1 uses one canonical prompt template for all providers and models. It must ask the primary model to perform language classification and conditional translation in a single round trip.

The prompt must include:

- target language: `en`
- English confidence threshold
- every block id, name, source language hint, and source text
- the exact internal JSON Schema the model must satisfy

The prompt must instruct the model to:

- report `detected_language` and estimate `english_confidence_estimate` for each block
- set `translation_required = false` and `translated_text = null` only when `english_confidence_estimate >= english_confidence_threshold`
- otherwise set `translation_required = true` and translate the full block into English
- preserve source meaning rather than summarize
- return exactly one `TranslatedBlock` for each input `Block`
- preserve input block order

Separate model-specific prompt templates are out of scope for v1. Provider/model overrides may tune the confidence rubric inside the canonical template.

## Translation Quality Contract

The translation prompt and validator must enforce these requirements:

- preserve source meaning
- do not summarize
- do not add interpretation
- preserve URLs, code identifiers, hashtags, handles, filenames, and quoted strings unless a natural-language part inside them is clearly meant to be translated
- preserve paragraph breaks when practical
- use natural English
- emit warnings for corrupt text, partially untranslatable fragments, schema-repair events, mixed-language ambiguity that affects translation quality, or provider/runtime issues
- return valid JSON that matches the requested schema

The translator should translate idioms into natural English when literal translation would obscure meaning.

## LLM Caller Adaptation

Translation must build one `curio-llm-request.v1` request and consume one `curio-llm-response.v1` response from [LLM-CALLER.md](LLM-CALLER.md).

The translation-to-LLM adapter should be a small pure mapping layer:

- build the translation prompt from `TranslationRequest`
- attach an internal translated-block JSON Schema derived from the public response schema
- require `text_generation` and `json_schema_output`
- pass provider, model, timeout, and request id through to the LLM caller
- validate the parsed LLM JSON into ordered `TranslatedBlock` values
- add the `llm` summary from the `LlmResponse` before returning `TranslationResponse`

The translation module should not import provider SDKs or shell out to provider CLIs.

## Translation Workflow

For each standalone translation request, Curio must:

1. validate the request shape
2. validate that target language is English
3. build an LLM request through the translation adapter
4. call the injected `LlmClient`
5. validate the LLM output against the expected translated-block contract
6. ensure every input `block_id` appears exactly once in output
7. ensure output block order matches input block order
8. ensure blocks with `english_confidence_estimate >= english_confidence_threshold` have `translation_required = false`
9. ensure all other blocks have `translation_required = true`
10. return the structured response

V1 should send all blocks for one artifact or dossier in one LLM request. Raw CLI text is represented as a single-block request. Curio must not batch unrelated artifacts together in one translation request. If a same-artifact request is too large for the selected provider, Curio should fail clearly rather than silently splitting the request.

For each dossier text block during Curio evaluation, Curio must:

1. assemble the normalized source-language text block
2. detect the block language through translation
3. assign the original block a unique numeric `block_id`
4. if the block counts as English, keep only the original block
5. otherwise translate the full normalized block into English
6. append the translated English text to `dossier_snapshot.evidence_text` as a paired block that references the original block by `translation_of`

## CLI Behavior

The standalone CLI behavior is defined in [CLI.md](CLI.md).

For raw single-block input without `--json`, the command should print only the translated English text.

If the source block is already English, the command should print the original text unchanged.

For JSON mode, the command should print the full `curio-translation-response.v1` object.

## Dossier Representation

`dossier_snapshot.evidence_text` remains an ordered array because it represents the ordered text shown to the evaluator.

Each block must carry:

- `block_id`
- `name`
- `language`
- `translation_of`
- `text`
- `was_truncated`
- `original_char_count`

When Curio translates a block:

- the original block remains present with `translation_of = null`
- the translated block contains the exact English text shown to the evaluator
- the translated block uses `language = en`
- the translated block uses the original name plus `_en`
- the translated block stores the original block's `block_id` in `translation_of`
- the translated block appears immediately after the original block in `dossier_snapshot.evidence_text`

When Curio does not translate a block:

- the original block remains present with `translation_of = null`
- the block's own `language` field records the detected language
- absence of a paired translated block means the original block was treated as English

Examples:

- `tweet_text` -> `tweet_text_en`
- `page_main_text` -> `page_main_text_en`
- `repo_readme` -> `repo_readme_en`

English blocks remain unpaired in v1.

## Validation And Retry

The translation service should validate LLM output before returning success.

It should reject:

- invalid JSON
- JSON that fails schema validation
- missing input block ids
- duplicate block ids
- block order changes
- English-classified blocks that also include translated text
- non-English-classified blocks without translated text
- unsupported target languages

Retries are owned by `curio.llm_caller`. The translation service should not implement its own retry loop. After LLM-caller retries are exhausted, translation should fail with the typed error returned by `curio.llm_caller`.

## Future Improvements

Future versions may add:

- local or smaller-model English classifiers before the primary translation model call
- preflight language detection that avoids LLM calls for clearly English text
- translation caching
- model-specific prompt overrides
- provider-specific prompt tuning based on observed failures
- splitting oversized same-artifact requests into deterministic chunks

## Out Of Scope

This document does not define:

- a non-English target language
- caching strategy
- post-translation human review UI
- downstream model behavior after dossier assembly

## Acceptance Scenarios

The translation spec is satisfied only if all of the following are true:

- raw CLI text can be translated to English
- structured JSON input can be translated to structured JSON output
- the same translation service can be called from the main Curio workflow
- translation can use either `openai_api` or `codex_cli` through `curio.llm_caller`
- translation classifies language and conditionally translates in one model round trip
- English blocks above the configured threshold remain untranslated
- low English-confidence estimates are translated rather than aborted and do not create warnings by themselves
- all blocks for one artifact or dossier can be translated in one request
- provider-specific details do not leak into `dossier_snapshot.evidence_text`
- English blocks remain unpaired in evaluation payloads
- non-English blocks produce adjacent `_en` paired blocks in evaluation payloads
- source text remains preserved when translation occurs
- full source text is translated before any dossier truncation
