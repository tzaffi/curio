# Curio Textify

## Purpose

`textify` converts non-text media artifacts into source-language text before
`translate` runs. It is a first-class workflow and reusable Python module:
`curio.textify`.

Pipeline position:

```text
download row -> artifact dossier extraction -> textify non-text media -> translate text blocks -> evaluate -> persist
```

## Public Module

The public module boundary mirrors `curio.translate`:

- `TextifyService`
- `TextifyRequest`
- `TextifyResponse`
- `Artifact`
- `TextifiedArtifact`
- `SuggestedTextFile`
- `TextifyError`, `TextifyRequestError`, `TextifyResponseError`
- `TEXTIFY_REQUEST_VERSION`, `TEXTIFY_RESPONSE_VERSION`

Workflow code owns contracts, prompts, validation, deterministic skip logic, and
response assembly. Provider-specific file handling stays in `curio.llm_caller`.

## Behavior

`textify` must:

- skip media that deterministic Curio extraction already handles as text
- convert supported non-text media into source-language text
- not translate, summarize, evaluate, label, or rank content
- preserve reading order and meaningful line breaks
- prefer Markdown for layout-rich artifacts
- prefer plain text or natural extensions for flat text, code, logs, and config
- suggest one or more safe relative output paths

Textified output is source-language text. Non-English or uncertain text must pass
through `translate` afterward.

## Contracts

Request JSON is defined by
[schemas/textify_request.schema.json](schemas/textify_request.schema.json).

Response JSON is defined by
[schemas/textify_response.schema.json](schemas/textify_response.schema.json).

Response statuses:

- `converted`
- `skipped_text_media`
- `unsupported_media`
- `no_text_found`

`llm` is nullable because all-text requests are valid no-ops.
When present, `llm.cost_estimate` mirrors the translate response. Token callers
use API-equivalent token pricing when configured. Document AI callers report
page usage through `usage.metered_objects` and can estimate page-priced cost
when page pricing is configured.

## Filename Policy

Each converted artifact returns `suggested_files`.

Rules:

- preserve visible filenames exactly, such as `foo.py`
- infer extensions from obvious code/config/log content when no filename is visible
- split multiple implied files into separate suggested files
- preserve implied relative directories only when visible or strongly implied
- reject unsafe paths: absolute paths, `..`, home expansion, drive roots, empty parts, and backslashes

Suggested paths are metadata. Curio does not write them unless a later explicit
command does so.

## Deterministic Text Detection

Text-media skip decisions are deterministic in v1. Curio uses explicit MIME
type, extension fallback, BOM-aware UTF-8 decoding, binary-byte checks, and a
conservative control-character threshold. It does not ask a model whether a file
is plaintext.

## Supported Media

V1 supports still images, PDFs, and document-like files supported by the chosen
provider. Unsupported media produces `unsupported_media` with a warning.

V1 punts audio transcription, video transcription, video frame extraction,
human OCR correction, broad OCR benchmark claims, OpenAI API direct textify
callers, and live Google Document AI smoke tests.

## Providers

V1 live-smoke-tests only Codex CLI. Codex receives image attachments through
`codex exec --image` and local-file metadata in the prompt.

Google Document AI is implemented behind the same `LlmClient` boundary with a
fakeable transport. It uses Application Default Credentials and sends raw bytes
only inside the provider transport.

## Acceptance Scenarios

- text media returns `skipped_text_media` and makes no provider call
- unsupported media returns `unsupported_media` and makes no provider call
- image media can produce Markdown text with a safe suggested path
- a code screenshot can produce a natural extension such as `.py` or `.sh`
- provider output is validated before response assembly
- `curio textify --json PATH` emits `curio-textify-response.v1`
- live smoke tests remain opt-in and skipped from default `make check`
