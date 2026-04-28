# curio
semantic labeling of iMsgX artifacts in preparation for a knowledgebase

## Specs

- [SCHEMA.md](SCHEMA.md) defines the Google Sheets workbook shape.
- [JSON-PAYLOAD.md](JSON-PAYLOAD.md) defines the persisted Drive JSON payload.
- [TRANSLATE.md](TRANSLATE.md) defines the translation workflow, standalone translate interface, and dossier translation representation.
- [TEXTIFY.md](TEXTIFY.md) defines the media-to-text workflow that runs before translation.
- [LLM-CALLER.md](LLM-CALLER.md) defines the provider-neutral LLM calling boundary used by translation and future workflows.
- [CLI.md](CLI.md) defines the top-level `curio` subcommand contract.
- [BOOTSTRAP.md](BOOTSTRAP.md) defines bootstrap label-registry runs.
- [AUTHENTICATION.md](AUTHENTICATION.md) defines local OpenAI/Codex secret storage and login setup.
- [USAGE.md](USAGE.md) explains `config.json`, checked-in config examples, and provider setup.
- [SMOKE-TESTS.md](SMOKE-TESTS.md) explains the opt-in live translation/textify smoke tests and evaluator workflow.
- [reports/translate-smoke/20260426-060103-22de460b22c0/UPSHOT.md](reports/translate-smoke/20260426-060103-22de460b22c0/UPSHOT.md) records the current translation model recommendation from the smoke/evaluator report.
- [reports/textify-smoke/20260428-132551-09c3fa3c8f75/UPSHOT.md](reports/textify-smoke/20260428-132551-09c3fa3c8f75/UPSHOT.md) records the current textify model recommendation from the smoke/evaluator report.
- [schemas/llm_request.schema.json](schemas/llm_request.schema.json) and [schemas/llm_response.schema.json](schemas/llm_response.schema.json) define the provider-neutral LLM JSON contracts.
- [schemas/translation_request.schema.json](schemas/translation_request.schema.json) and [schemas/translation_response.schema.json](schemas/translation_response.schema.json) define the standalone translation JSON contracts.
- [schemas/textify_request.schema.json](schemas/textify_request.schema.json) and [schemas/textify_response.schema.json](schemas/textify_response.schema.json) define the standalone textify JSON contracts.

## Configuration

Copy one checked-in example to `config.json`, then edit it for your machine:

```bash
cp config.example.codex_cli.json config.json
# or
cp config.example.openai_api.json config.json
# or, for Google Document AI textify experiments
cp config.example.google_document_ai.json config.json
```

Curio reads `config.json` at runtime; it does not fall back to example files.
Raw secrets belong in Keychain, not in `config.json`.
