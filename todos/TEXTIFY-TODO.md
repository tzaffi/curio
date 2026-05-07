# Curio Textify Implementation TODO

## ONE SHOTTING

Zeph is going to sleep now. You should implement all the Checkpoints except that you should not run any live smoke tests. So do not stop to ask for any guidance. When the urge occurs to ask for guidance, take extra time to research what the best answer would be given the goals of this document. It is expected that at the end of the one-shotting session, all of the checkpoints through and including 8F will have been successfully completed. 8G will have been started including the new Makefile targets `textify-smoke-evaluate` and `textify-smoke-report`. However, these commands WILL NOT HAVE BEEN EXECUTED.

## Legend

- [x] Done in this planning pass
- [~] Current review boundary / paused for guidance
- [ ] Not started
- [lock] Must not start until the previous step is reviewed and passes `make check`
- [test] Requires `make check`: Ruff, Ty, pytest, 100% coverage
- [live] Requires explicit live opt-in; never part of default `make check`

## Completed

[x] **Checkpoint 0: Translate implementation review and textify scope baseline**

- Reviewed the final `translate` shape across:
  - `TODO-TRANSLATE.md`
  - `TRANSLATE.md`
  - `LLM-CALLER.md`
  - `CLI.md`
  - `USAGE.md`
  - `SMOKE-TESTS.md`
  - `src/curio/translate`
  - `src/curio/llm_caller`
  - `tests/test_translate*.py`
  - `tests/live_smoke_helpers.py`
  - `tests/live_smoke_evaluator.py`
  - `tests/test_translate_live_smoke.py`
  - `reports/translate-smoke/20260426-060103-22de460b22c0/UPSHOT.md`
- Captured the translate lessons that must carry into textify:
  - workflow code owns contracts, prompt policy, validation, and service behavior
  - `translate` is an exportable Python module, not only a CLI path
  - `curio.translate.__init__` exports the public service, request/response models, errors, constants, and helper surface
  - provider-specific behavior stays inside `curio.llm_caller`
  - CLI code only parses, resolves config, calls a service, and renders output
  - named `llm_callers` are the runtime selection boundary
  - live smoke tests are skipped by default and are never part of `make check`
  - retained smoke outputs and a separate evaluator pass drive model recommendations
  - provider config must be explicit; no silent model/auth fallback
  - prompts must be checked-in or built-in, placeholder-validated, and workflow-specific
  - response JSON now includes nullable `llm.cost_estimate` when configured pricing and provider usage support it
  - non-JSON CLI output supports colored warning/stats stderr through `--suppress-warnings` and `--stats`
  - secret values must never appear in payloads, exceptions, stdout, stderr, or retained reports
- Checked current official provider docs for the first smoke-test candidate matrix:
  - OpenAI model docs currently recommend `gpt-5.5` for complex work and `gpt-5.4-mini` / `gpt-5.4-nano` for lower cost and latency.
  - OpenAI model docs currently list latest models as supporting text and image input with text output, multilingual capabilities, and vision.
  - `gpt-5.5` is documented as the flagship/frontier candidate and costs `$5.00` input, `$0.50` cached input, and `$30.00` output per 1M text tokens.
  - `gpt-5.4-nano` is documented for cheap high-volume data extraction style tasks and costs `$0.20` input, `$0.02` cached input, and `$1.25` output per 1M text tokens.
  - `gpt-5.4-mini` costs `$0.75` input, `$0.075` cached input, and `$4.50` output per 1M text tokens.
  - `gpt-5.3-codex` costs `$1.75` input, `$0.175` cached input, and `$14.00` output per 1M text tokens.
  - `gpt-5.4` costs `$2.50` input, `$0.25` cached input, and `$15.00` output per 1M text tokens.
  - Live Codex CLI ChatGPT auth later rejected `gpt-5.4-nano`, `gpt-5-nano`, `gpt-5-mini`, `gpt-4.1-mini`, `gpt-4o-mini`, and `gpt-5.3-chat-latest`; `gpt-5.3-codex` was accepted and added as the cost/quality comparison model.
  - Codex CLI `0.125.0` documents `codex exec --image <FILE>...` for image attachments; non-image media handoff still needs a dedicated protocol research checkpoint before locking `LlmRequest` media parts.
  - OpenAI Responses file input supports file URLs, uploaded file IDs, and base64 file data, but direct OpenAI API textify remains punted until intentionally designed.
  - Google Document AI supports PDF, GIF, TIFF, JPEG, PNG, BMP, WebP, HTML, DOCX, PPTX, and XLSX/XLSM in the relevant processor docs, with HTML/OOXML tied to Layout Parser support.
  - Google Document AI online processing uses provider-side raw document bytes plus MIME type; Curio should read bytes only inside the Google provider transport.
  - Google Document AI Enterprise Document OCR pricing is currently `$1.50` per 1,000 pages for the first 5M pages/month and `$0.60` per 1,000 pages after that; Layout Parser is currently `$10` per 1,000 pages.
  - Google Document AI samples show `Document.text`, pages, blocks, paragraphs, lines, tokens, detected languages, and text anchors as the response primitives Curio should map from.
  - Podcast transcript support is not a single obvious platform API; post-v1 research should compare OpenAI speech-to-text, Deepgram prerecorded audio, AssemblyAI transcription/diarization, and any podcast-platform transcript APIs available at that time.
- Research sources to re-check before implementation, because model availability and prices are time-sensitive:
  - OpenAI models: `https://developers.openai.com/api/docs/models`
  - GPT-5.5: `https://developers.openai.com/api/docs/models/gpt-5.5`
  - GPT-5.4 nano: `https://developers.openai.com/api/docs/models/gpt-5.4-nano`
  - GPT-5.4 mini: `https://developers.openai.com/api/docs/models/gpt-5.4-mini`
  - GPT-5.3-Codex: `https://developers.openai.com/api/docs/models/gpt-5.3-codex`
  - GPT-5.4: `https://developers.openai.com/api/docs/models/gpt-5.4`
  - OpenAI file inputs: `https://developers.openai.com/api/docs/guides/file-inputs`
  - Google Document AI pricing: `https://cloud.google.com/document-ai/pricing`
  - Google Document AI supported files: `https://docs.cloud.google.com/document-ai/docs/file-types`
  - Google Document AI process documents: `https://docs.cloud.google.com/document-ai/docs/process-documents-client-libraries`
  - Google Document AI OCR sample: `https://docs.cloud.google.com/document-ai/docs/samples/documentai-process-ocr-document`
  - Google Document AI Layout Parser: `https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk`
  - Supadata transcripts: `https://supadata.ai/`
  - OpenAI speech-to-text: `https://platform.openai.com/docs/guides/speech-to-text`
  - Deepgram prerecorded audio: `https://developers.deepgram.com/docs/pre-recorded-audio`
  - AssemblyAI speaker diarization: `https://www.assemblyai.com/docs/speech-to-text/pre-recorded-audio/speaker-diarization`

[~] **Current pause**

- Checkpoint 8 is complete.
- `make check` passes with 100% coverage.
- `make textify-smoke` passed with 73 selected live textify tests.
- `make textify-smoke-evaluate` produced the retained evaluator matrix.
- Durable report artifacts live under `reports/textify-smoke/20260428-132551-09c3fa3c8f75/`.
- The remaining punt is live Google Document AI smoke testing.

## Goal

Introduce a first-class Curio `textify` subcommand and reusable `curio.textify`
module.

`textify` is the media-to-text step that runs in the final Curio pipeline
immediately before `translate`.

Pipeline order:

```text
download row -> artifact dossier extraction -> textify non-text media -> translate text blocks -> evaluate -> persist
```

The rule is deliberately narrow:

- text media is ignored by `textify`
- non-text media is converted into source-language text
- `textify` must not translate
- `textify` must not summarize
- `textify` must not label, rank, or evaluate
- `translate` remains the only component that converts source-language text into English

Most textified outputs should be Markdown. Plain `.txt` output is preferred when
the source is essentially a flat text file captured as media, such as a
screenshot of a plain text note, command output, log, or simple code/text file.

Textify must also suggest output filenames. The suggestion is part of the
textified result, not just CLI sugar:

- If the source visibly names a file, preserve that exact filename, for example `foo.py`.
- If the language or format is obvious but no filename is visible, infer the extension and choose a short purpose-based filename.
- If multiple files are implied, return multiple suggested files.
- If an implicit directory structure is visible or strongly implied, return a relative path such as `scripts/install.sh`.
- Most extracted files are still expected to be Markdown; code, shell scripts, logs, plain text, and config snippets should use their natural extension when clear.
- Suggested paths must be relative, normalized, and safe to write only if a later command explicitly writes them.

## Design Principles

The v1 textify workflow should follow these rules:

- `textify` is a first-class Curio capability, not an implementation detail of evaluation.
- `textify` converts one source artifact into source-language text that `translate` can handle.
- `textify` skips a source that is already text media or has already produced deterministic `evidence_text`.
- `textify` preserves source content; it does not translate, summarize, normalize claims, or infer labels.
- Markdown is the default structured text format for layout-rich artifacts.
- Plain text is valid and preferred when Markdown would add fake structure.
- Suggested filenames, extensions, and relative paths are first-class output, including multiple suggested files from one source artifact.
- Output format selection is part of the response contract and must be testable.
- Text-media detection must be deterministic by default; only use a nondeterministic model for this decision if a later checkpoint demonstrates a materially better method.
- Curio preserves original media metadata in the dossier `details`; textified text becomes normal `evidence_text`.
- Provider-specific file handling, OCR, vision, auth, and API behavior stay inside `curio.llm_caller`.
- Codex CLI is the only v1 live-smoke-tested textify provider.
- Google Document AI must still be implemented behind the same caller boundary with fake transport tests and best-effort production correctness.
- Default checks must remain offline: no auth, network, API keys, Google ADC, `codex` binary, or live media processing.

## Required Scope Decisions

V1 should support:

- still images: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.tif`, `.tiff`, `.bmp`
- PDFs
- document-like files where the provider supports them: `.docx`, `.pptx`, `.xlsx`, `.xlsm`, `.html`
- multi-page documents where the provider can process them without silent truncation
- source-language text preservation for non-English media

V1 should punt:

- audio transcription
- video transcription
- deterministic frame extraction from video
- human-in-the-loop OCR correction
- broad benchmark claims about OCR quality
- OpenAI API direct textify callers
- live Google Document AI smoke tests

Post-v1 roadmap notes belong in `ROADMAP.md`. The first item after v1 should
be YouTube/social video transcript retrieval through Supadata/SuperData before
attempting video-frame OCR. Podcast transcript support also needs API research,
with OpenAI speech-to-text, Deepgram prerecorded audio, AssemblyAI
transcription/diarization, and platform transcript APIs as initial candidates.

Unsupported media should produce a clear skipped/unsupported result with a
warning. It must not silently call `translate`, invent text, or upload raw bytes
into retained smoke artifacts.

## Planned Contract Sketch

The exact schema belongs in `TEXTIFY.md` and
`schemas/textify_request.schema.json`, but the target shape should be close to
this.

Request:

```json
{
  "textify_request_version": "curio-textify-request.v1",
  "request_id": "textify-20260426-000001",
  "preferred_output_format": "auto",
  "source": {
    "path": "/absolute/path/to/screenshot.png",
    "name": "screenshot.png",
    "mime_type": "image/png",
    "sha256": "hex-sha256",
    "source_language_hint": null,
    "context": {
      "source_kind": "image"
    }
  },
  "llm_caller": null
}
```

Response:

```json
{
  "textify_response_version": "curio-textify-response.v1",
  "request_id": "textify-20260426-000001",
  "source": {
    "name": "screenshot.png",
    "input_mime_type": "image/png",
    "source_sha256": "hex-sha256",
    "textification_required": true,
    "status": "converted",
    "suggested_files": [
      {
        "suggested_path": "notes/screenshot-summary.md",
        "output_format": "markdown",
        "text": "# Heading\n\nExtracted source-language text."
      }
    ],
    "detected_languages": ["en"],
    "page_count": 1,
    "warnings": []
  },
  "llm": {
    "provider": "codex_cli",
    "model": "gpt-5.4-mini",
    "usage": {
      "input_tokens": 800,
      "cached_input_tokens": null,
      "output_tokens": 220,
      "reasoning_tokens": null,
      "total_tokens": 1020,
      "metered_objects": [],
      "started_at": "2026-04-26T12:00:00Z",
      "completed_at": "2026-04-26T12:00:08Z",
      "wall_seconds": 8.0,
      "thinking_seconds": null
    },
    "cost_estimate": null
  },
  "warnings": []
}
```

Important differences from `translate`:

- Textify accepts exactly one source per request; mixed or multi-artifact requests are invalid.
- `llm` may be `null` when the source is skipped as already-text media.
- `status` must distinguish `converted`, `skipped_text_media`, `unsupported_media`, and `no_text_found`.
- `suggested_files` is non-empty only when `status = converted`.
- Each suggested file has `suggested_path`, `output_format`, and `text`.
- `output_format` is `markdown`, `txt`, or a natural extension-backed format such as `py`, `sh`, `json`, `yaml`, `toml`, or `log`; `auto` is request-only.
- Suggested paths must be relative, normalized, non-empty, and must not contain `..`, home-directory expansion, drive roots, or absolute path syntax.
- `page_count` is provider-observed when available and `null` otherwise.
- `llm.cost_estimate` should mirror the translate response when token pricing is configured and usage supports it.
- Google Document AI page billing must be represented through `metered_objects` and a page-aware cost estimate, not guessed token usage.

## Completed Checkpoint 0 Notes From Translate

Textify should copy these proven translate patterns almost mechanically:

- frozen slotted dataclasses for request/response records
- explicit `from_json()` and `to_json()` methods
- schema validation through `curio.schemas.validate_json`
- a small pure adapter that builds `LlmRequest`
- an injected `LlmClient` in `TextifyService`
- fake-client service tests before real provider calls
- strict provider output validation before response assembly
- CLI input-mode exclusivity
- compact runtime and usage errors
- nullable response cost estimates from configured caller pricing
- `--suppress-warnings`, `--stats`, red warning stderr, and green stats stderr
- named caller selection by CLI, structured JSON, then `config.json`
- checked-in example configs
- offline helper tests for smoke-retention code
- skipped-by-default live smoke markers
- retained smoke outputs under `tmp/textify-smoke/{run_id}/`
- durable human reports under `reports/textify-smoke/{run_id}/`

Textify must not copy these translate assumptions:

- `text_generation` is not the only provider capability.
- `LlmRequest.input` cannot remain text-only if Codex and Google Document AI must process local media files.
- prompt placeholders cannot remain translation-only.
- every successful response cannot require an LLM/provider call, because an already-text source is a valid no-op.
- token usage is not sufficient for cost accounting, because Document AI bills by page.
- one input source may produce multiple suggested output files.

## Checkpoint 1: Normative Textify Spec

[lock] [x] **1A: Add `TEXTIFY.md`**

- Define the normative v1 textify behavior.
- Include:
  - purpose and non-goals
  - reusable module boundary: `curio.textify`
  - public exports matching the translate pattern:
    - `TextifyService`
    - `TextifyRequest`
    - `TextifyResponse`
    - `TextifySource`
    - `TextifiedSource`
    - `SuggestedTextFile`
    - textify errors and constants
  - request and response contracts
  - text media skip policy
  - media support matrix
  - output format policy: `markdown`, `txt`, and request-time `auto`
  - suggested filename/path policy
  - no-translation/no-summary fidelity contract
  - dossier representation after textification
  - relationship to `translate`
  - validation and retry ownership
  - provider boundary through `curio.llm_caller`
  - acceptance scenarios
- State explicitly that textification output is source-language text and must pass through `translate` afterward when language is non-English or uncertain.
- State explicitly that text media already handled by deterministic Curio extraction bypasses `textify`.
- [test] Gate: docs-only patch does not need new tests, but `make check` must still pass before continuing.

[lock] [x] **1B: Update existing normative docs**

- Update `CLI.md` to reserve and specify `textify`.
- Update `LLM-CALLER.md` to describe non-classic provider support and media/file content parts.
- Update `JSON-PAYLOAD.md` to explain how textified media becomes `dossier_snapshot.evidence_text`.
- Update `SCHEMA.md` only if Sheets semantics change; they probably should not.
- Update `ROADMAP.md` only if the post-v1 transcript items are not already present.
- Update `README.md` spec links only after `TEXTIFY.md` exists.
- Keep all changes descriptive; no code yet.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 1.5: Media Handoff Protocol Research

[lock] [x] **1.5A: Codex CLI, OpenAI API, and Google Document AI media handoff research**

- Complete this before finalizing `LlmRequest` media/file content parts.
- Research the exact current protocol for each provider:
  - Codex CLI:
    - supported `codex exec --image <FILE>...` behavior
    - whether PDFs or other files are supported as attachments
    - whether non-image media must be read from the sandboxed filesystem
    - path visibility rules for `--cd`, `--add-dir`, read-only sandbox, and output schema usage
    - JSONL usage behavior when images are attached
  - OpenAI API:
    - Responses API `input_file` support through `file_id`, `file_url`, and base64 `file_data`
    - supported MIME types and file-size/page limits
    - whether image/PDF/file upload support should remain punted or become a future direct textify caller
  - Google Document AI:
    - `RawDocument` byte upload shape
    - batch vs online processing limits
    - MIME support by processor type
    - region/processor endpoint behavior
    - page-count and pricing signals available from response metadata
- Produce a short research note inside this TODO before implementation continues.
- The note must decide the exact `LlmRequest` local file/media representation, including whether Codex uses attachments, filesystem paths, or both.
- The note must decide which provider clients own byte reads and which provider clients receive paths only.
- No production code in this checkpoint.
- [test] Gate: docs-only patch does not need new tests, but `make check` must still pass before continuing.

## Checkpoint 2: Pure Textify Contracts

[lock] [x] **2A: JSON schemas**

- Add:
  - `schemas/textify_request.schema.json`
  - `schemas/textify_response.schema.json`
- Register them in `curio.schemas.SchemaName`.
- Use draft 2020-12 like existing schemas.
- Include closed enums for:
  - `preferred_output_format`: `auto`, `markdown`, `txt`
  - response `output_format`: `markdown`, `txt`, `null`
  - `status`: `converted`, `skipped_text_media`, `unsupported_media`, `no_text_found`
- Reuse or mirror `llmUsage` / `llmSummary`, but allow `llm = null`.
- Include nullable `llm.cost_estimate` like the current translation response.
- Allow `metered_objects` and cost estimates to carry Document AI page usage.
- Model `suggested_files` as an array on each converted source:
  - `suggested_path`
  - `output_format`
  - `text`
- Require at least one suggested file when `status = converted`.
- Require zero suggested files for skipped, unsupported, and no-text results.
- Do not include raw file bytes or base64 in request or response JSON.
- [test] Add schema tests.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **2B: `curio.textify.models`**

- Add frozen slotted dataclasses:
  - `TextifyRequest`
  - `TextifySource`
  - `TextifyResponse`
  - `TextifiedSource`
  - `SuggestedTextFile`
  - `TextifyLlmSummary` or reuse the translation `LlmSummary` pattern if it moves to a shared module
- Add typed errors:
  - `TextifyError`
  - `TextifyRequestError`
  - `TextifyResponseError`
- Add `to_json()` / `from_json()`.
- Enforce:
  - non-empty request id
  - non-empty names
  - absolute source paths for runtime requests
  - supported format enum values
  - converted sources must have at least one suggested file
  - skipped, unsupported, and no-text sources must have no suggested files
  - each suggested file has a non-empty relative path, output format, and text
  - suggested paths must be normalized and must reject absolute paths, `..`, empty parts, home expansion, and platform drive roots
  - output extensions should agree with `output_format` when the format maps cleanly to an extension
  - no duplicate warnings
- [test] Add serialization and invariant tests.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **2C: Deterministic media classification helpers**

- Add pure helpers for:
  - MIME/type normalization
  - extension fallback when MIME type is missing
  - deterministic plaintext detection
  - text-media skip decisions
  - provider-supported media decisions
  - default output-format hinting
  - SHA-256 calculation for local files
- Text-media skip policy should treat these as no-op when they are already handled upstream:
  - existing `dossier_snapshot.evidence_text` blocks
  - UTF-8 text/plain and text/markdown files
  - source JSON/HTML/README text that current deterministic extractors already handle
- Deterministic plaintext detection should use:
  - explicit MIME type when trustworthy
  - extension fallback
  - BOM-aware UTF-8 decoding
  - binary-byte and control-character checks
  - a conservative maximum undecodable/control-character threshold
- Do not call a model to decide whether a file is plaintext in v1.
- Non-text media should include images, PDFs, and supported document formats.
- Do not add a MIME-sniffing dependency unless tests prove `mimetypes` and explicit request MIME are insufficient.
- [test] Add classification tests with no real provider calls.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 3: Textify Adapter, Validation, And Service With Fake Client

[lock] [x] **3A: Textify model-output schema and prompt templates**

- Add `curio.textify.adapter`.
- Add built-in textifier prompt templates.
- The prompt must instruct Codex to:
  - inspect only the supplied media source
  - extract visible/readable source-language text
  - not translate
  - not summarize
  - preserve reading order
  - preserve line breaks where meaningful
  - use Markdown for headings, lists, tables, and document structure
  - use plain text when the source is a flat text/log/code screenshot
  - suggest one or more output files with safe relative paths
  - preserve visible filenames exactly when present
  - infer extensions from obvious code/config/content when no filename is visible
  - split multiple implied files into separate suggested file records
  - preserve implicit directory structure only as relative paths
  - return exactly one output record for the supplied source
  - emit compact warnings for uncertain OCR, low image quality, rotated/cropped text, unreadable regions, or provider/runtime issues
- Add `build_textify_template_values()`.
- Add `build_textify_llm_request()`.
- Required capabilities should be textify-specific, not translation-specific.
- [test] Add adapter tests for prompt contents, metadata, schema shape, and required capabilities.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **3B: Prompt-template validation generalization**

- Refactor `curio.config.LlmCallerPromptConfig` so translate placeholders remain strict and textify placeholders can also be strict.
- Do not weaken validation to "any placeholder is allowed."
- Supported textify placeholders should include only the fields actually used by the adapter, likely:
  - `textify_request_json`
  - `output_schema_json`
  - `request_id`
  - `preferred_output_format`
  - `source_manifest_json`
  - `suggested_file_policy`
- Preserve existing translate placeholders:
  - `translation_request_json`
  - `output_schema_json`
  - `request_id`
  - `target_language`
  - `english_confidence_threshold`
- Add either workflow-aware prompt validation or a narrow union with tests proving invalid placeholders still fail.
- [test] Update config tests for translate and textify prompt overrides.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **3C: Textify output validation**

- Add `curio.textify.validation`.
- Validate provider output before response assembly.
- Enforce:
  - response request id matches
  - one output record for the supplied non-skipped/non-unsupported source
  - output source name matches input name
  - `converted` records have at least one suggested file
  - suggested files have non-empty `suggested_path`, `output_format`, and `text`
  - suggested paths are safe relative paths
  - skipped, unsupported, and no-text records have no suggested files
  - Markdown output must not be wrapped in a single useless code fence unless the source is code/log text
  - warnings remain compact
- Keep retry policy out of textify; retries belong to `llm_caller`.
- [test] Add validation tests matching the translate validation style.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **3D: `TextifyService.textify()` with fake client**

- Wire:
  - request validation
  - deterministic skip/unsupported decisions
  - LLM request construction only for a source requiring conversion
  - injected fake `LlmClient`
  - provider output validation
  - response assembly
  - `llm = null` for skipped text-media sources
- Do not call a provider for already-text sources.
- Do not batch unrelated sources together.
- Same-source multi-file output is allowed through `suggested_files`.
- [test] Add fake-client service tests.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **3E: Service integration polish**

- Review public API names, error messages, and imports.
- Export only the intended public boundary from `curio.textify`, mirroring `curio.translate.__all__`.
- Keep validation internals private.
- Keep service methods small and inspectable, matching `TranslationService`.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 4: LLM Caller Foundation Adjustments For Media/Textification

[lock] [x] **4A: Provider and capability model updates**

- Add provider name:
  - `google_document_ai`
- Add capabilities as needed, likely:
  - `file_input`
  - `image_input`
  - `pdf_input`
  - `document_text_extraction`
  - `ocr`
  - `layout_extraction`
  - `markdown_output`
  - `plain_text_output`
  - `suggested_file_output`
  - `multiple_file_output`
  - `relative_path_output`
  - `metered_page_usage`
- Update `schemas/llm_request.schema.json` and `schemas/llm_response.schema.json`.
- Existing `translate` requests must be unchanged except for the expanded enum definitions.
- Missing required media capabilities must fail before subprocess or network work begins.
- [test] Add capability tests, including OpenAI API rejection for textify-required file/media capabilities if OpenAI API is not implemented for textify.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **4B: Local file content parts**

- Extend `LlmRequest.input` beyond text-only content.
- Add a local file content part with:
  - `type = local_file`
  - absolute `path`
  - `mime_type`
  - `sha256`
  - optional `name`
- Finalize this shape only after Checkpoint 1.5 decides exact provider handoff protocols.
- Do not include raw bytes in stable LLM request JSON.
- Update:
  - dataclasses
  - JSON schemas
  - `from_json()` / `to_json()`
  - provider clients
  - tests
- Codex CLI should format local file parts into the prompt and preserve file metadata.
- Google Document AI should read the file bytes only inside the provider client.
- OpenAI API should reject unsupported local file parts unless a future checkpoint intentionally implements file uploads.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **4C: Codex CLI media/file support**

- Update `CodexCliClient` to satisfy textify-required capabilities when configured.
- Define a strict file-access policy:
  - every local file path must exist
  - every local file path must match the request SHA-256 before the provider call
  - paths must be under the selected Codex working directory or another explicit allowed root
  - fail clearly rather than copying files silently
- Update `build_codex_exec_prompt()` so local files are named and inspectable.
- Preserve `--output-schema`, `--json`, `--ephemeral`, read-only sandbox, explicit `--cd`, and existing schema-sanitization behavior.
- Investigate whether Codex CLI can inspect every intended file type directly; if a type is not supported, fail during capability/media validation.
- [test] Use fake runner tests only.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **4D: Shared usage and cost accounting**

- Ensure `LlmUsage.metered_objects` supports page counts cleanly.
- Add helper conventions for:
  - token-cost records
  - page-cost records
  - mixed token/page records if a future provider uses both
- Extend or supplement `LlmCostEstimate` so textify can represent:
  - token API-equivalent costs for Codex
  - page-based Document AI costs
  - unavailable costs when pricing or usage is incomplete
- Do not guess token counts for Google Document AI.
- Do not guess page counts for Codex.
- [test] Add unit tests for metered page usage serialization and cost helpers.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 5: Google Document AI Caller

[lock] [x] **5A: Google Document AI auth/config contracts**

- Add `GoogleDocumentAiAuthConfig`.
- V1 auth should use Google Application Default Credentials.
- Do not store service account JSON or access tokens in Curio config.
- Config should include non-secret routing metadata:
  - project id
  - location, such as `us` or `eu`
  - processor id
  - optional processor version
  - processor kind: `enterprise_document_ocr` or `layout_parser`
  - optional timeout
  - optional process options
- Add config examples only after the parser and factory paths work with fakes.
- Add clear errors for missing ADC, missing project/location/processor id, invalid processor kind, and unsupported processor versions.
- [test] Add config parsing tests with no Google calls.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **5B: Google Document AI client with fake transport**

- Add `src/curio/llm_caller/google_document_ai.py`.
- Add a fakeable transport boundary, similar to `OpenAiApiTransport`.
- Add runtime dependency through `uv` only when this checkpoint starts:
  - likely `google-cloud-documentai`
- Production behavior:
  - construct `DocumentProcessorServiceClient`
  - set regional API endpoint from location
  - read local file bytes at call time
  - call `process_document`
  - map returned `Document` to Curio JSON output
  - map page count to `metered_objects`
  - map detected languages when present
  - map provider errors into Curio typed errors
- Output mapping:
  - Enterprise OCR should use `Document.text`, pages, paragraphs, lines, tokens, and text anchors.
  - Layout Parser should prefer layout/chunk structures when available for Markdown.
  - If table/list/title structure is not available, fall back to stable reading-order text.
  - Use `txt` for flat OCR when structure confidence is low or the artifact appears to be a plain text screenshot.
  - Use `markdown` when headings, lists, tables, pages, or document hierarchy are meaningful.
- No live Google calls in tests.
- [test] Add fake-response tests for OCR, layout, no text found, low quality warnings, unsupported MIME, auth, timeout, and invalid output.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **5C: Provider factory integration**

- Extend `ProviderClientFactory` to construct `GoogleDocumentAiClient`.
- Ensure named caller config can select:
  - `textifier_google_docai_ocr`
  - `textifier_google_docai_layout`
- Keep `translate` unaffected.
- Fail if a translation workflow selects `google_document_ai`, because Document AI does not satisfy translation capabilities.
- Fail if a textify workflow selects a caller that lacks textify capabilities.
- [test] Add factory tests.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **5D: Best-effort Google Document AI production review**

- Before marking Checkpoint 5 complete, re-check current Google docs:
  - supported file types
  - processor list
  - OCR options
  - Layout Parser options
  - online processing limits
  - pricing
  - ADC setup
- Confirm response parsing against current Python client object names.
- Confirm no secrets or raw bytes appear in logs, exceptions, stdout, stderr, retained smoke records, or JSON payloads.
- Confirm Google-specific behavior stays inside `curio.llm_caller`.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 6: CLI `textify`

[lock] [x] **6A: CLI input modes**

- Add `curio textify`.
- Support exactly one input mode:
  - positional artifact path
  - `--input-file PATH`
  - `--input-json PATH`
- Current implementation supports positional artifact path, `--input-file PATH`, and `--input-json PATH`.
- Do not support raw stdin bytes in v1 unless a safe MIME and SHA policy is designed.
- Raw path input builds a one-source request.
- `--input-file PATH` should build the same one-source request shape as positional path input.
- Structured JSON input uses `curio-textify-request.v1`.
- Include flags:
  - `--json`
  - `--suppress-warnings`
  - `--stats`
  - `--output PATH`
  - `--config PATH`
  - `--mime-type MIME`
  - `--preferred-output-format auto|markdown|txt`
  - `--source-language LANG`
  - `--llm-caller NAME`
- Add `textify.llm_caller` config default.
- Resolution precedence should be:
  1. CLI `--llm-caller`
  2. structured JSON `llm_caller`
  3. `config.json` `textify.llm_caller`
- If the source is skipped as text media, the CLI should exit 0.
- For one skipped source without `--json`, print a compact red diagnostic on stderr explaining that deterministic text media was skipped, and print no stdout text.
- For converted single-source input without `--json`, stdout should contain the rendered text of the single suggested file plus trailing newline.
- For converted input that produces multiple suggested files, non-JSON mode may fall back to the full response JSON; this is accepted behavior for v1.
- For structured input or `--json`, stdout should contain the full textify response JSON.
- In non-JSON mode, warning output should be red and suppressible by `--suppress-warnings`.
- In non-JSON mode, `--stats` should print provider, model, usage, wall time, metered objects, and cost estimate to stderr in green, matching translate's current behavior.
- [test] Add CLI tests with fake service/client injection, matching translate coverage style.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **6B: Output writing**

- `--output PATH` writes rendered text for single converted source in non-JSON mode.
- `--output PATH` writes full response JSON in JSON mode.
- For multi-suggested-file non-JSON input, writing the full response JSON is accepted v1 behavior.
- Do not create sidecar output files in v1 without explicit flags.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **6C: Config examples and usage docs**

- Add checked-in Codex config examples for textify callers.
- Add checked-in Google Document AI config examples after fake transport tests pass.
- Update `USAGE.md` with:
  - `textify.llm_caller`
  - Codex CLI textify setup
  - Google ADC setup
  - Google Document AI processor setup fields
  - pricing fields for Codex token estimates and Google page estimates
  - supported/unsupported media notes
  - examples for Markdown, plain text, and inferred code/config filenames
- Update `AUTHENTICATION.md` for Google ADC, without raw credential storage in repo files.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 7: Curio Pipeline Integration

[lock] [x] **7A: Dossier assembly contract**

- Update future dossier assembly logic so non-text media passes through `textify` before `translate`.
- Existing text media should continue directly to `translate`.
- Textified source-language blocks should be inserted into `dossier_snapshot.evidence_text` as ordinary source blocks:
  - `translation_of = null`
  - `language = detected language or source hint or und`
  - `name` should come from the safe suggested path when useful, normalized into a stable block name
  - `text = textified source-language text from each suggested file`
  - `was_truncated` and `original_char_count` reflect the textified text
- Multiple suggested files from one source become multiple ordered source blocks unless a later dossier design needs grouping metadata.
- If `translate` later produces English, the `_en` paired block behavior remains exactly as defined in `TRANSLATE.md`.
- Store audit metadata for textification in `dossier_snapshot.details`, not by adding large new Sheets columns.
- [test] Add dossier assembly tests when the curate/dossier module exists.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **7B: Textification warnings policy**

- Warnings from textify should remain compact.
- Candidate warning codes:
  - `textify_low_image_quality`
  - `textify_rotated_or_cropped_text`
  - `textify_partial_ocr`
  - `textify_no_readable_text`
  - `textify_unsupported_media`
  - `textify_provider_warning`
- Full provider payloads do not belong in Sheets.
- Human-facing retained reports may include enough evidence to debug quality without storing raw media bytes.
- [test] Gate: `make check`, 100% coverage.

## Checkpoint 8: Opt-In Codex CLI Live Textify Smoke Harness

[lock] [x] **8A: Smoke-test case intake and matrix**

- Build this as small, reviewable sub-checkpoints.
- Live tests must be skipped by default.
- Default `make check` must remain fully offline.
- The active live smoke scope is Codex CLI only.
- Do not run Google Document AI live smoke tests in v1.
- The first generated-only matrix was too synthetic to distinguish model quality; keep it as low-weight baseline coverage only.
- Add `Model Importance` as a 1-10 integer used for model-ranking totals.
- Existing synthetic/generated rows have `Model Importance = 1`.
- JSON, HTML, and ZIP cases are coverage-only and do not affect model-ranking totals because they are skipped or rejected without an LLM call.
- `C-IMG-MULTI-01` is only a weak baseline for multi-file output because it is shallow, synthetic, and homogeneous.
- Real fixtures live under `tests/fixtures/textify_smoke/real/`; the generated directory-tree composite lives under `tests/fixtures/textify_smoke/generated/`.
- Include at least these cases:

| Case ID | Source / Owner | Input Mode | Media Scenario | Expected Output | Assertions | Model Importance | Notes |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `C-IMG-TXT-01` | Codex | artifact path | PNG image of a plain text note or terminal output | `txt` preserving lines exactly enough for downstream translation | response schema, `converted`, `output_format = txt`, line/order preservation, no Markdown headings invented | 1 | Synthetic baseline for the user's explicit `.txt` preference case |
| `C-IMG-CODE-01` | Codex | artifact path | Screenshot of a Python script with visible filename `foo.py` | suggested file path exactly `foo.py`, text preserving code | response schema, filename preservation, extension preservation, code text fidelity | 1 | Synthetic baseline for explicit filename extraction |
| `C-IMG-CODE-02` | Codex | artifact path | Screenshot of a Python script without filename | suggested `.py` filename based on script purpose | response schema, extension inference, safe relative filename, code text fidelity | 1 | Synthetic baseline for inferred filename and extension |
| `C-IMG-MULTI-01` | Codex | artifact path | Screenshot showing three concatenated shell scripts with implied paths | three suggested `.sh` files with safe relative paths | response schema, multiple suggested files, relative path validation | 1 | Weak synthetic baseline for multiple file output |
| `C-IMG-POST-01` | Codex | artifact path | Social/media screenshot with handle, timestamp, URL, emoji, and non-English text | Markdown or text preserving visible text and source language | response schema, no translation, handle/URL/emoji preservation | 1 | Synthetic source-language preservation baseline |
| `C-PDF-DOC-01` | Codex | artifact path | One-page PDF with title, headings, paragraphs, bullets | Markdown with heading/list structure | response schema, `output_format = markdown`, reading order, heading/list preservation | 1 | Synthetic document layout baseline |
| `C-PDF-TABLE-01` | Codex | artifact path | PDF with a small table and surrounding prose | Markdown table when table structure is recoverable | response schema, table cell preservation, no row/column swaps | 1 | Synthetic table layout baseline |
| `C-IMG-RECEIPT-01` | Codex | artifact path | Receipt/form-like image with labels, amounts, and dates | Markdown or text with stable key lines/table | response schema, amounts/dates preservation | 1 | Synthetic dense OCR baseline |
| `C-IMG-NO-TEXT-01` | Codex | artifact path | Image with no readable text | `status = no_text_found`, `text = null`, compact warning | response schema, no invented description | 1 | Synthetic hallucination guard |
| `C-TEXT-NOOP-01` | Curio deterministic | artifact path | Already-text source file | `skipped_text_media`, no stdout in non-JSON mode, no provider call | response schema, `llm = null`, compact warning | 1 | Synthetic no-op guard without mixed media |
| `R-IMG-DASH-01` | iMsgX download | artifact path | Real dense Claude Code usage dashboard screenshot | Markdown summary preserving dashboard title, filters, metric cards, charts, recent-session table | response schema, numeric value preservation, chart/table extraction | 9 | Dense dark dashboard with charts, numbers, tiny table text |
| `R-IMG-LLM-TABLE-01` | iMsgX download | artifact path | Real local LLM cheat-sheet infographic table | Markdown table preserving model rows, weights, speed, context, use cases, bottom line | response schema, table structure, row/column preservation | 10 | Very dense infographic table; strong discriminator |
| `R-IMG-INFOGRAPHIC-01` | iMsgX download | artifact path | Real Hermes Agent chalkboard-style infographic | Structured Markdown preserving commands, section labels, provider lists, gateway labels | response schema, tiny label preservation, code snippet preservation | 10 | Many tiny labels, code snippets, nonstandard visual layout |
| `R-IMG-PAPER-PAGE-01` | iMsgX download | artifact path | Real academic paper page screenshot with figure | Markdown with title, authors, link, abstract, figure caption, major diagram labels | response schema, reading order, figure label preservation | 9 | Academic page screenshot with small text and figure |
| `R-IMG-CHARTS-01` | iMsgX download | artifact path | Real two-panel benchmark chart screenshot | Markdown tables for both benchmark charts and percentages | response schema, chart label and percentage preservation | 8 | Chart OCR plus ranking/percentage preservation |
| `R-IMG-TERMINAL-01` | iMsgX download | artifact path | Real terminal listing screenshot | Plain text/log preserving command lines, listing columns, filenames | response schema, monospaced text preservation | 8 | Dense terminal output |
| `R-IMG-ASCII-DIAGRAM-01` | iMsgX download | artifact path | Real ASCII-style diagram screenshot | Plain text preserving diagram layout and result box | response schema, layout fidelity, no summary-only output | 8 | Layout fidelity matters more than prose summary |
| `R-IMG-COMPARISON-TABLE-01` | iMsgX download | artifact path | Real OpenClaw/Hermes/Paperclip comparison table | Markdown table preserving Dimension/OpenClaw/Hermes/Paperclip columns | response schema, row/column preservation | 8 | Real comparison table with dense cells |
| `R-IMG-NO-TEXT-REAL-01` | iMsgX download | artifact path | Real photo with no readable text | `status = no_text_found`, no invented visual description | response schema, no hallucinated alt text | 5 | Real no-text hallucination guard |
| `C-IMG-DIR-TREE-01` | Codex generated from iMsgX PNGs | artifact path | One composite PNG representing a nested directory of files | exactly `home/important/openclaw-rl.md`, `home/important/agent-comparison.md`, `home/trivial/claude-code-listing.log` | response schema, exactly three suggested files, safe relative paths only, nested dirs preserved, no cross-section bleed, no extra files | 10 | Critical single-source-to-directory behavior |
| `R-PDF-PAPER-01` | iMsgX download | artifact path | Real long scientific PDF | Markdown preserving title, abstract, sections, table/figure captions, reading order | response schema, PDF structure extraction | 10 | Long scientific PDF with tables, references, layout |
| `R-HTML-ARXIV-01` | iMsgX download | artifact path | Real arXiv HTML page | coverage-only `skipped_text_media`, no LLM call | response schema, no provider call | 1 | Covers HTML source behavior |
| `R-HTML-GITHUB-README-01` | iMsgX download | artifact path | Real complex GitHub README HTML page | coverage-only `skipped_text_media`, no LLM call | response schema, no provider call | 1 | Covers complex HTML source behavior |
| `R-JSON-XARTICLE-CODE-01` | iMsgX download | artifact path | Real X article JSON containing code blocks | coverage-only `skipped_text_media`, no LLM call | response schema, no provider call | 1 | Covers structured JSON source behavior |
| `R-ZIP-REPO-01` | iMsgX download | artifact path | Real GitHub repo ZIP archive | coverage-only `unsupported_media`, warning, no LLM call | response schema, no provider call | 1 | Covers archive rejection behavior |

- For each case, capture:
  - stable case id
  - exact fixture path
  - MIME type
  - fixture SHA-256
  - expected output format
  - expected suggested file paths
  - expected human-readable extraction intent
  - preservation requirements
  - model importance
  - whether it participates in model ranking
  - source basename/provenance for checked-in real fixtures
  - assertion style
  - local prerequisites
- Reviewed and approved before live smoke execution.

[lock] [x] **8B: Codex model and config comparison matrix**

- Propose exactly three Codex named callers for the first textify live matrix.
- Re-check OpenAI model docs immediately before implementation because model availability and pricing can change.
- Final reviewed candidates after local Codex availability checks:
  - `textifier_codex_gpt_54_mini`
  - `textifier_codex_gpt_53_codex`
  - `textifier_codex_gpt_55`
- Zeph explicitly accepted `gpt-5.5` as the third first-pass textify candidate instead of `gpt-5.4`.
- Zeph explicitly accepted `gpt-5.3-codex` as the replacement comparison candidate after Codex CLI ChatGPT auth rejected `gpt-5.4-nano`.
- Document `gpt-5.5` pricing and capability as the frontier candidate and evaluator candidate.
- Rationale:
  - textification is mostly OCR, reading order, and structure extraction, not deep reasoning
  - `gpt-5.4-mini` is the current translate default and likely the best first default candidate if nano is unavailable or too lossy
  - `gpt-5.3-codex` gives a Codex-optimized middle-cost comparison point for quality and cost
  - `gpt-5.5` is the frontier reliability candidate for difficult layout and OCR
- `gpt-5.4-nano` was not available in local Codex CLI with ChatGPT auth and was replaced before the retained live matrix.

| Caller | Model | Reasoning Effort | Verbosity | Prompt Policy | Purpose | Cost | Runtime Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `textifier_codex_gpt_54_mini` | `gpt-5.4-mini` | `low` | `low` | checked-in textifier prompt | expected default candidate | `(input * $0.75 + cached_input * $0.075 + output * $4.50) / 1M` | Faster |
| `textifier_codex_gpt_53_codex` | `gpt-5.3-codex` | `low` | default | checked-in textifier prompt | Codex-optimized cost/quality comparison | `(input * $1.75 + cached_input * $0.175 + output * $14.00) / 1M` | Middle |
| `textifier_codex_gpt_55` | `gpt-5.5` | `low` | default | checked-in textifier prompt | frontier reliability candidate | `(input * $5.00 + cached_input * $0.50 + output * $30.00) / 1M` | Slower |

- Cost formula conventions:
  - use retained token usage from live Codex responses
  - compute API-equivalent cost as `(input_tokens * input_price + cached_input_tokens * cached_input_price + output_tokens * output_price) / 1_000_000`
  - if cached input is unavailable, use `0` cached input tokens and treat all input as regular input
  - do not include Google Document AI page pricing in Codex model comparisons
- Reviewed and approved before implementation.

[lock] [x] **8C: Retention and evaluator matrix design**

- Retain live smoke artifacts under `tmp/textify-smoke/{run_id}/`.
- Use `run_id = YYYYMMDD-HHMMSS-{short_sha_or_nogit}`.
- Do not commit raw retained smoke artifacts by default.
- Retain, per run:
  - case id
  - named caller
  - source fixture metadata, not raw media bytes in evaluator JSONL
  - full textify request JSON
  - full textify response JSON
  - rendered text output
  - warnings
  - token/timing usage
  - command/config metadata with secrets redacted
- Artifact layout:
  - `manifest.json`
  - `cases/{case_id}/expected.md`
  - `runs/{case_id}/{caller}/request.json`
  - `runs/{case_id}/{caller}/response.json`
  - `runs/{case_id}/{caller}/textified.md` or `textified.txt`
  - `runs/{case_id}/{caller}/usage.json`
  - `runs/{case_id}/{caller}/stderr.txt`
  - `evaluation/evaluator-input.jsonl`
  - `evaluation/evaluator-output.md`
- `evaluator-input.jsonl` object fields:
  - `case_id`
  - `caller`
  - `fixture_metadata`
  - `expected_textification_intent`
  - `ground_truth_text`
  - `expected_output_format`
  - `expected_suggested_paths`
  - `preservation_requirements`
  - `status`
  - `output_format`
  - `suggested_files`
  - `rendered_textified_text`
  - `response_warnings`
  - `usage`
  - `response_path`
- Define evaluator workflow using Codex `gpt-5.5` with `model_reasoning_effort = xhigh`.
- Evaluator must judge extraction fidelity, not whether the source content is useful or true.
- Evaluator must not reward translation or summarization.
- Evaluator matrix template:

| Case ID | Caller | Cost | OCR/Text Fidelity | Reading Order | Structure/Format | Filename/Path Fit | Non-Hallucination | Total | Preferred? | Warnings / Failures | Evaluator Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `{case_id}` | `{caller}` | `$api_equivalent_cost_usd` from `usage.json` | integer 1-5 | integer 1-5 | integer 1-5 | integer 1-5 | integer 1-5 | sum of five scores | `yes` for exactly one caller per case unless all are unusable | concrete warning/failure summary or `none` | concise rationale |

- Preferred output rule:
  - mark exactly one preferred caller per case unless all outputs are unusable
  - prefer the lowest-cost output among tied quality scores
  - explain ties or no-preference outcomes in evaluator notes
- Reviewed and approved before implementation.

[lock] [x] **8D: Offline-safe pytest opt-in plumbing**

- Add a `live_codex_cli_textify` pytest marker or generalize the existing live Codex marker with workflow-specific selection.
- Preferred explicit marker:
  - `live_codex_cli_textify`
- Add exact opt-in env var:
  - `CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS=1`
- Skipped collection must not:
  - import runtime secrets
  - load real Google or Codex config files
  - touch network
  - call `codex`
  - instantiate subprocess runners
- Add offline tests for marker registration and exact env semantics.
- Keep default `make check` independent of real media providers.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **8E: Codex CLI live textify harness helpers**

- Codex can generate the missing deterministic fixture set; Zeph does not need to provide external examples unless real-world coverage is desired.
- Required fixture coverage remains:
  - text screenshot
  - code screenshot with visible filename
  - code screenshot without filename
  - multi-file shell-script screenshot
  - social/non-English screenshot
  - PDF document
  - PDF table
  - receipt/form-like image
  - no-text image
  - single-source plaintext no-op
- Add test-only helpers for:
  - loading explicit runtime config
  - selecting textifier Codex callers
  - constructing textify service calls
  - retaining evaluator-ready outputs
  - computing API-equivalent token costs
  - preserving suggested file arrays in evaluator records
  - redacting caller summaries
  - rendering textified output
- Do not put live-smoke helper behavior in production modules unless production code actually needs it.
- Cover helpers with offline fake tests.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **8F: Codex CLI live smoke tests**

- Use generated deterministic fixtures for the reviewed coverage set unless Zeph supplies real-world fixtures before implementation.
- Add skipped-by-default live tests from the reviewed matrix.
- Verify every reviewed smoke case can run against each reviewed Codex named caller.
- Verify `curio textify --llm-caller textifier_codex_gpt_54_mini` works through explicit config selection.
- Verify `curio textify` works through configured `textify.llm_caller`.
- Verify checked-in prompt templates are loaded through `llm_callers.NAME.prompt`.
- Retain inputs and outputs in the reviewed retention format.
- Fail with clear operator guidance when:
  - `codex` is missing
  - Codex login is absent
  - config is missing
  - fixture path is outside allowed Codex read roots
  - live opt-in is incomplete
  - model lacks needed media/file support
- Add Makefile targets:
  - `make textify-smoke`
  - `make textify-smoke-collect`
- [test] Gate: `make check`, then optional live run by explicit opt-in.

[lock] [x] **8F.5: Single-source textify contract correction**

- Block live smoke/evaluator work until textify accepts exactly one source per request.
- Replace public request JSON `artifacts: [...]` with singular `source: {...}`.
- Require only `source.path` in structured JSON; keep `name`, `mime_type`, `sha256`, `source_language_hint`, and `context` as optional source metadata.
- Replace public response JSON `artifacts: [...]` with singular `source: {...}` containing status, warnings, detected languages, and `suggested_files`.
- Keep multiple `suggested_files` allowed, but require all suggested files to come from the single source.
- Do not preserve legacy `artifacts` input compatibility in textify schema or CLI.
- Leave `llm_caller` internals free to support richer multi-file/media requests; textify passes exactly one source into them.
- Remove mixed-media smoke coverage and replace it with `C-TEXT-NOOP-01`.
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **8G: Evaluator grading pass**

- Retained passing live smoke outputs under `tmp/textify-smoke/20260428-132551-09c3fa3c8f75/`.
- Ran `make textify-smoke-evaluate TEXTIFY_SMOKE_RUN=tmp/textify-smoke/20260428-132551-09c3fa3c8f75`.
- Used Codex `gpt-5.5` with Extra High reasoning effort.
- Evaluator graded 72 case/caller textify outputs.
- Published durable report artifacts under `reports/textify-smoke/20260428-132551-09c3fa3c8f75/`.
- Added `UPSHOT.md` with:
  - default recommendation: `textifier_codex_gpt_54_mini`
  - escalation recommendation: `textifier_codex_gpt_55` for long, high-value PDFs
  - do-not-default recommendation: `textifier_codex_gpt_53_codex`
  - cost summary
  - known failure cases and rerun policy
- Kept evaluator results separate from pass/fail smoke assertions; model-quality misses remain evaluator-scored.
- Added and validated Makefile targets:
  - `make textify-smoke-evaluate`
  - `make textify-smoke-report`
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **8H: Live smoke operator docs**

- Added textify smoke docs in `SMOKE-TESTS.md`.
- Included:
  - reviewed media/case matrix
  - reviewed model/config matrix
  - commands
  - artifact locations
  - Codex prerequisites
  - media fixture notes
  - prompt-template notes
  - common failures
  - evaluator workflow
  - report/upshot policy
- Cross-linked:
  - `TEXTIFY.md`
  - `AUTHENTICATION.md`
  - `USAGE.md`
  - `LLM-CALLER.md`
  - `TRANSLATE.md`
  - `reports/textify-smoke/20260428-132551-09c3fa3c8f75/UPSHOT.md`
- [test] Gate: `make check`, 100% coverage.

[lock] [x] **8I: Final smoke harness review**

- Ran `make check` with live tests skipped.
- Ran the reviewed live smoke matrix:
  - `make textify-smoke`
  - result: 73 passed, 305 deselected in 21m37s
- Ran the evaluator pass and recorded the output matrix.
- Confirmed:
  - no secrets in stdout/stderr/exceptions observed
  - no raw media bytes in evaluator JSONL
  - retained outputs are sufficient for quality review
  - docs match actual commands, config names, markers, and environment variables
  - `UPSHOT.md` makes a concrete recommendation
- Fixed two live-run issues during final review:
  - `C-IMG-NO-TEXT-01` expected status now matches the reviewed `no_text_found` intent
  - duplicate provider/runtime warnings are deduplicated before `LlmResponse`
  - unsupported media warning now lives only on `response.source.warnings`
- Checkpoint 8 is complete.
- [test] Gate: `make check`, 100% coverage.

## PUNT

[lock] [ ] **Google Document AI live smoke tests**

- Punt live Google Document AI smoke tests out of v1.
- Later, decide whether to add `CURIO_LIVE_GOOGLE_DOCUMENT_AI_TESTS=1`.
- Later, run the same media fixture matrix through `textifier_google_docai_ocr` and `textifier_google_docai_layout`.
- Later, compare Google page costs to Codex token costs.
- Later, document Google Cloud project, processor, quota, region, and billing prerequisites.
- Later, ensure retained reports do not expose Google credentials, processor internals, or raw media bytes.

[lock] [ ] **OpenAI API direct textify callers**

- Punt direct OpenAI API textify callers out of v1.
- The OpenAI API client currently handles text-only message parts.
- If direct OpenAI textify becomes useful, design file upload / image input handling explicitly instead of smuggling paths into text prompts.
- Keep `openai_api` unsupported for textify-required capabilities until that design exists.

[lock] [ ] **Video and audio media**

- Punt video frame extraction, audio transcription, and speech-to-text out of v1.
- Do not add ffmpeg, video thumbnailing, or audio transcription as side effects of textify.
- Add a separate media-prep design before supporting those artifact classes.

## Hard Rules

- Do not implement textify by weakening `translate`.
- Do not put provider-specific code in `curio.textify`.
- Do not make Google Document AI special cases leak into dossier/evaluation code.
- Do not silently copy media files for Codex access.
- Do not store raw media bytes in stable JSON request/response payloads.
- Do not store raw Google credentials in repo files, config examples, logs, payloads, or retained reports.
- Do not call `translate` from `textify`.
- Do not translate, summarize, or evaluate in textify prompts.
- Do not add live tests to default `make check`.
- Use `uv` for Python execution.
- Every implementation checkpoint must pass `make check` with 100% coverage.
- Pause after every major checkpoint for review, following the `translate` implementation discipline.
