# curio
semantic labeling of iMsgX artifacts in preparation for a knowledgebase

## Specs

- [SCHEMA.md](SCHEMA.md) defines the Google Sheets workbook shape.
- [JSON-PAYLOAD.md](JSON-PAYLOAD.md) defines the persisted Drive JSON payload.
- [TRANSLATE.md](TRANSLATE.md) defines the translation workflow, standalone translate interface, and dossier translation representation.
- [LLM-CALLER.md](LLM-CALLER.md) defines the provider-neutral LLM calling boundary used by translation and future workflows.
- [CLI.md](CLI.md) defines the top-level `curio` subcommand contract.
- [BOOTSTRAP.md](BOOTSTRAP.md) defines bootstrap label-registry runs.
- [schemas/llm_request.schema.json](schemas/llm_request.schema.json) and [schemas/llm_response.schema.json](schemas/llm_response.schema.json) define the provider-neutral LLM JSON contracts.
- [schemas/translation_request.schema.json](schemas/translation_request.schema.json) and [schemas/translation_response.schema.json](schemas/translation_response.schema.json) define the standalone translation JSON contracts.
