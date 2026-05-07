# Curio Translate Implementation TODO

## Legend

- ✅ Done and passing `make check` at 100% coverage
- 🟡 Current review boundary / paused for guidance
- ⬜ Not started
- 🔒 Must not start until the previous step is reviewed and passes `make check`
- 🧪 Requires `make check`: Ruff, Ty, pytest, 100% coverage

## Completed

✅ **Checkpoint 1: Freeze spec baseline**

- Validated all existing JSON schemas through `uv`.
- Confirmed clean baseline before package work.

✅ **Checkpoint 2: Package scaffold**

- Added `pyproject.toml`, `uv.lock`, `Makefile`, `src/curio`, Typer entrypoint, and scaffold tests.
- Reserved CLI commands: `translate`, `curate`, `bootstrap`, `schema`, `doctor`.
- 🧪 Passed `make check` with 100% coverage.

✅ **Checkpoint 3: Pure contracts**

- Added provider-neutral LLM contracts.
- Added translation request/response contracts.
- Added Curio schema loading/validation helpers.
- Added tests for serialization, schema validation, protocol use, and core invariants.
- 🧪 Passed `make check` with 100% coverage.

✅ **Checkpoint 3 cleanup: contract shape review**

- Removed auth modes from `LlmCapability`; auth remains provider configuration.
- Removed unused `LlmAuthMode`.
- Converted `curio.llm_caller` and `curio.translate` into subpackages.
- Renamed internals to idiomatic module names: `models.py` and `service.py`.
- Removed unnecessary `from __future__ import annotations`.
- Kept validation local to each subpackage; behavior matches across packages.
- 🧪 Passed `make check` with 100% coverage.

🟡 **Current pause**

- Checkpoint 8I is the current review boundary.
- Review final smoke harness state before marking Checkpoint 8 complete.
- Do not run live Codex CLI smoke tests without explicit opt-in.

## Completed Checkpoint 4

✅ **4A: JSON parsing helpers**

- Add explicit parser/from-JSON functions for current contracts.
- Parse and validate `TranslationRequest`, `TranslatedBlock`, `LlmUsage`, `LlmResponse`, and related nested objects.
- Use `curio.schemas.validate_json` from non-test code where appropriate.
- Preserve current public import paths.
- 🧪 Passed `make check` with 100% coverage.

✅ **4B: Translation-to-LLM request adapter**

- Build a provider-neutral `LlmRequest` from `TranslationRequest`.
- Include canonical translation instructions, request JSON, threshold, target language, and block data.
- Attach the internal translated-block JSON Schema requested by `TRANSLATE.md`.
- Require only `text_generation` and `json_schema_output`.
- Pass through `request_id`, `model`, and `timeout_seconds`.
- No actual service call yet.
- 🧪 Passed `make check` with 100% coverage.

✅ **4C: LLM output validation**

- Validate model output before response assembly.
- Enforce one output block per input block.
- Reject missing, duplicate, extra, or reordered block IDs.
- Enforce threshold behavior:
  - English above threshold means `translation_required = false` and `translated_text = null`.
  - Anything else means `translation_required = true` and non-empty `translated_text`.
- Keep retry policy out of translation; retries belong to `llm_caller`.
- 🧪 Passed `make check` with 100% coverage.

✅ **4D: `TranslationService.translate()` with fake client**

- Wire request validation, LLM request adapter, injected fake `LlmClient`, LLM output validation, and `TranslationResponse` assembly.
- Add `llm` summary from `LlmResponse`.
- Preserve block order and request-level warnings.
- Still no real provider calls.
- 🧪 Passed `make check` with 100% coverage.

✅ **4E: Service integration polish**

- Review public API ergonomics after fake-client service tests.
- Tighten names, errors, and test fixtures before CLI/provider work.
- Removed stale `TranslationNotImplementedError`.
- Stopped exporting validation internals and JSON type aliases from `curio.translate`.
- Made `TranslationService.translate()` assembly steps easier to inspect.
- Replaced inline service fake classes with a reusable local recording fake.
- 🧪 Passed `make check` with 100% coverage.

## Completed Checkpoints 5-6

✅ **Checkpoint 5: CLI translate**

- Raw positional text, stdin, `--input-file`, and `--input-json`.
- Enforce exactly one input mode.
- Support `--json`, `--output`, provider/model/timeout flags.
- Use fake or injected service first; do not require live LLM calls for tests.
- Added concise usage/runtime errors with exit code 2/1.
- Raw single-block output prints translated text, or original text when already English.
- Structured input and `--json` print `curio-translation-response.v1` JSON.
- Default provider client remains a clear not-implemented runtime error until checkpoint 6.
- 🧪 Passed `make check` with 100% coverage.

✅ **Checkpoint 6: Provider auth configuration and docs**

- Add `AUTHENTICATION.md`.
  - Write it as an "explain it like I'm 5" operator guide.
  - Include direct OpenAI links:
    - API key dashboard: https://platform.openai.com/api-keys
    - API authentication docs: https://developers.openai.com/api/reference/overview#authentication
    - Codex authentication docs: https://developers.openai.com/codex/auth
    - Codex CLI + Sign in with ChatGPT help: https://help.openai.com/en/articles/11381614
  - Walk through creating/retrieving the OpenAI API key from the OpenAI account interface.
  - Walk through seeding that API key into macOS Keychain.
  - Walk through Codex CLI ChatGPT login and how to make Codex store cached credentials in the OS keyring.
  - Explain when re-authentication is expected: revoked token, expired/invalid session, changed scopes/settings, or explicit logout.
- Add `keyring` as a runtime dependency through `uv`.
- Model auth after `forwarder` and `iMsgX`:
  - use a `SecretStore` protocol.
  - use `KeyringSecretStore` for runtime.
  - use `InMemorySecretStore` for tests.
  - keep secret locator metadata separate from secret values.
- Add provider auth/config contracts outside `LlmCapability`.
- Keep auth out of `LlmRequest.required_capabilities`.
- Define how CLI/config resolves auth for each provider.
- Do not use environment variables as the normal secret path.
- Do not accept raw secret values as CLI flags.
- `openai_api` auth:
  - store API keys in Keychain, not repo files, shell profiles, or environment variables.
  - use locator metadata such as `service = curio/openai-api`, `account = default-api-key` unless we choose a better naming convention.
  - load the API key from `SecretStore` only at provider-client call time.
  - keep the key out of request/response JSON, logs, exceptions, and terminal output.
- `codex_cli` auth:
  - support ChatGPT login by relying on Codex CLI's own cached credentials.
  - require or document Codex config `cli_auth_credentials_store = "keyring"` so Codex stores cached credentials in the OS credential store.
  - do not copy Codex OAuth/access/refresh tokens into Curio-owned storage unless a later design explicitly proves this is necessary and safe.
  - support API-key mode only through a secure path: either Codex's own keyring-backed login or Curio Keychain lookup passed to Codex without logging/leaking.
  - investigate local `codex login --help` / current Codex docs before choosing the exact API-key handoff.
- Add narrow typed auth/config errors.
- Add tests proving secret values do not appear in payloads, exceptions, stdout, or stderr.
- Keep translation contracts provider-neutral.
- Added `curio.llm_caller.auth` contracts and secret-store adapters.
- Added public auth exports from `curio.llm_caller`.
- Added auth tests with in-memory and mocked Keyring stores.
- Confirmed local `codex login --help` supports `--with-api-key` from stdin and `--device-auth`.
- 🧪 Passed `make check` with 100% coverage.

🔒 🟨 **Checkpoint 7: Provider clients**

✅ **7A: Provider client foundation**

- Added provider-client config metadata.
- Added shared local mechanics inside `curio.llm_caller`: capability enforcement, timing helper, response construction helpers, and typed error mapping conventions.
- Did not add real OpenAI SDK calls.
- Did not add a real `codex` subprocess call.
- Tested that missing capabilities fail before any runner or transport is touched.
- 🧪 Passed `make check` with 100% coverage.

✅ **7B: Codex CLI parser and command builder**

- Implemented pure command construction for `codex exec`.
- Implemented JSONL event parsing from fake Codex output.
- Extracted final JSON output and usage from fixture events.
- Locked down exactly what Curio expects from `codex exec --json`.
- Did not execute a real subprocess.
- 🧪 Passed `make check` with 100% coverage.

✅ **7C: CodexCliClient with fake subprocess runner**

- Added `CodexCliClient` using an injectable subprocess runner.
- Handled timeout, non-zero exit, missing executable, invalid JSON, and schema-invalid output.
- Supported ChatGPT/cached auth by relying on Codex CLI state without reading Codex auth files.
- Kept Codex API-key login or handoff isolated because it requires side-effectful `codex login --with-api-key`.
- 🧪 Passed `make check` with 100% coverage.

✅ **7D: OpenAiApiClient with fake transport**

- Added OpenAI SDK dependency with `uv`.
- Added `OpenAiApiClient` using a fakeable transport/client boundary.
- Mapped `LlmRequest` to the Responses API with structured JSON Schema output.
- Resolved API keys from `SecretStore` only at call time.
- Tested without network or real API keys.
- Tested that secrets never appear in payloads, exceptions, stdout, or stderr.
- 🧪 Passed `make check` with 100% coverage.

✅ **7E: Provider factory and CLI integration**

- Replaced `_ProviderClientNotImplemented` with `ProviderClientFactory`.
- Wired `curio translate --provider codex_cli|openai_api` to construct the selected client.
- Injected explicit provider auth/config into clients.
- Kept provider-specific behavior inside `curio.llm_caller`; `curio.translate` stayed unchanged.
- Preserved compact CLI errors for provider factory/runtime failures.
- 🧪 Passed `make check` with 100% coverage.

✅ **7E.5: Explicit provider runtime config cleanup**

- Removed silent provider/auth/client fallbacks from the production factory path.
- Removed `default_provider_auth_config` so missing auth cannot be synthesized indirectly.
- Added `config.json` loading with fail-fast validation.
- Added checked-in provider examples:
  - `config.example.codex_cli.json`
  - `config.example.openai_api.json`
- Added `USAGE.md` for config setup, provider value discovery, and expected fail-fast behavior.
- Required explicit provider config for CLI provider construction.
- Required explicit model selection before Codex CLI/OpenAI API provider calls.
- Required explicit Codex CLI working directory instead of inheriting subprocess CWD.
- Tightened `CodexCliClient`, `ProviderClientFactory`, and `build_codex_exec_command` so Codex always receives an explicit `--cd`.
- 🧪 Passed `make check` with 100% coverage.

✅ **7E.6: Named LLM caller configurations**

- Replace provider-level runtime configuration with named `llm_callers` configuration entries.
- Each named LLM caller config owns:
  - provider: `codex_cli` or `openai_api`
  - model
  - auth config
  - timeout_seconds
  - provider-specific runtime tuning
  - optional translator prompt overrides
- Remove runtime model override semantics from translation:
  - remove `--model`
  - replace `--provider` with `--llm-caller NAME`
  - replace translation request `provider`/`model` fields with `llm_caller`
  - do not add `default_model`
- Rename or supplement factory APIs so callers are built by named config, not provider enum alone.
- Allow multiple active named configs for the same provider with different models/tuning, for example:
  - `translator_codex_gpt_55`
  - `translator_codex_gpt_54_mini`
  - `translator_openai_gpt_54_mini_cold`
- Add Codex CLI tuning inside each Codex caller config:
  - `model_reasoning_effort`: `minimal | low | medium | high | xhigh`
  - `model_verbosity`: `low | medium | high`
  - map non-null values to `codex exec --config model_reasoning_effort="..."` and `--config model_verbosity="..."`
  - do not add Codex `temperature`; official Codex config does not document it
  - emit no empty `--config` entries
- Add OpenAI Responses API tuning inside each OpenAI caller config:
  - `temperature`: number from `0` to `2`
  - `reasoning_effort`: `none | minimal | low | medium | high | xhigh`
  - `max_output_tokens`: positive integer or null
  - `text_verbosity`: `low | medium | high`
  - map non-null values to `temperature`, `reasoning.effort`, `max_output_tokens`, and `text.verbosity`
- Update `config.example.codex_cli.json` and `config.example.openai_api.json` to use named `llm_callers`.
- Add optional `llm_callers.NAME.prompt.instructions` and `llm_callers.NAME.prompt.user` translator prompt templates.
- Include the default translator prompt templates in the checked-in `translator_*` example caller configs.
- Validate prompt templates against supported placeholders only:
  - `translation_request_json`
  - `output_schema_json`
  - `request_id`
  - `target_language`
  - `english_confidence_threshold`
- Update docs to explain named caller selection, provider-specific tuning, and translator prompt overrides.
- Update tests for config parsing, named caller selection, multiple same-provider configs, command construction, OpenAI payload construction, invalid tuning values, prompt overrides, and no empty argument emission.
- 🧪 Passed `make check` with 100% coverage.

🔒 🟨 **Checkpoint 8: Opt-in Codex CLI live smoke test harness**

- Build this as small, reviewable sub-checkpoints.
- Whole-checkpoint acceptance:
  - live tests are skipped by default
  - `make check` remains fully offline
  - default checks do not require auth, network, API keys, `codex login`, or a real `codex` binary
  - live smoke tests can be run manually against `codex_cli`
  - translation inputs and provider outputs are retained for evaluator review
  - Codex ChatGPT 5.5 Extra High effort can grade translation results into an output matrix
  - docs explain prerequisites, opt-in variables, expected runtime/network behavior, and troubleshooting

✅ **8A: Smoke-test case intake and matrix**

- Zeph provides high-quality smoke-test cases based on prior research.
- Codex proposes additional smoke-test cases that cover gaps in Zeph's examples.
- Convert Zeph-provided and Codex-proposed cases into an explicit smoke-test matrix before writing harness code.
- For each case, capture:
  - stable case id
  - input mode: raw text, stdin, input file, or structured JSON
  - source-language scenario: English pass-through, clear non-English translation, low-confidence English, mixed language, URLs/code/handles preservation, or multi-block ordering
  - source text or fixture reference
  - expected human-readable translation intent
  - expected assertion style: exact JSON contract checks, semantic translation checks, warning checks, or CLI output checks
  - required local prerequisites: config file, `translate.llm_caller`, auth state, `codex` binary, network, and expected timeout
- Prefer a compact but varied matrix that supports model/config comparison without turning smoke tests into broad translation benchmarking.
- Include the reviewed matrix table directly in this TODO before implementation, using this shape:

| Case ID   | Source / Owner | Input Mode      | Scenario                                                                | Source Text / Fixture                                                                                                                | Expected Translation Intent                                                                                                                                                   | Assertions                                                                                                                          | Notes                                                               |
| --------- | -------------- | --------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `Z-CN-01` | Zeph           | structured JSON | Chinese, multi-paragraph tech/product thread, URLs, handle, SSH command | Full source input from user example 1: Hermes WebUI thread                                                                           | Translate into natural English while preserving `ssh -N -L 8787:127.0.0.1:8787 user@your.server.com`, `http://localhost:8787`, GitHub URLs, product names, and `@nesquena`    | Response schema, one output block, `translation_required = true`, URL/code/handle preservation, semantic adequacy                   | Strong case for preserving commands and links                       |
| `Z-CN-02` | Zeph           | raw text        | Chinese tech explainer, numerals, slash commands, tool names            | Full source input from user example 2: Addy Osmani Agent Skills thread                                                               | Translate into clear English while preserving `Agent Skills`, `18000`, `/spec`, `/plan`, `/build`, `/test`, `/ship`, Claude Code, Gemini CLI, Codex, Cursor                   | Response schema, `translation_required = true`, command/tool-name preservation, semantic adequacy                                   | Good workflow vocabulary case                                       |
| `Z-EN-01` | Zeph           | raw text        | English pass-through, hype/claims, hardware names                       | Full source input from user example 3: open weights/local hardware thread                                                            | Treat as English and leave untranslated; do not normalize claims or rewrite tone                                                                                              | Response schema, `translation_required = false`, `translated_text = null`, original text emitted for non-JSON CLI output            | English classifier/pass-through baseline                            |
| `Z-KO-01` | Zeph           | structured JSON | Korean with mixed English model/tool names and bullets                  | Full source input from user example 4: local LLM setup                                                                               | Translate Korean portions while preserving `MacStudio M2 Ultra 64gb`, `SuperQwen3.6 35b mlx 4bit`, `90tok/s`, `Ernie Image Turbo`, `Hermes Agent + MLX-LM`, GPT Codex, Gemini | Response schema, `translation_required = true`, bullet structure meaning, model/tool preservation                                   | Mixed Korean/English technical shorthand                            |
| `Z-AR-01` | Zeph           | raw text        | Arabic RTL, colloquial phrasing, English technical terms                | Full source input from user example 5: Qwen3.6 local AI argument                                                                     | Translate into idiomatic English while preserving Alibaba, Qwen3.6, MoE, 35B, 3B, Inference, Enterprise, Local Agents, Cloud APIs                                             | Response schema, `translation_required = true`, technical-term preservation, semantic adequacy                                      | RTL plus code-switching                                             |
| `Z-HE-01` | Zeph           | raw text        | Hebrew RTL, political/security statement                                | Full source input from user example 6: thanks to soldiers/security and peace                                                         | Translate accurately into English without adding context, softening, or intensifying political language                                                                       | Response schema, `translation_required = true`, semantic adequacy, tone preservation                                                | Sensitive public/political language                                 |
| `Z-HE-02` | Zeph           | raw text        | Hebrew RTL, graphic invective/profanity                                 | Full source input from user example 7: graphic hostile text                                                                          | Translate accurately into English while preserving abusive/graphic tone without sanitizing, escalating, or adding new slurs                                                   | Response schema, `translation_required = true`, semantic adequacy, tone preservation, no extra warning unless model flags ambiguity | Stress case for offensive content fidelity                          |
| `C-JA-01` | Codex          | raw text        | Japanese product announcement, emoji, date/time, hashtag, URL           | `明日 10:00 JST に v2.1 を公開します。README.md と /deploy を確認してね 🚀 #Hermes https://example.com/release`                      | Translate Japanese into concise English while preserving `10:00 JST`, `v2.1`, `README.md`, `/deploy`, emoji, hashtag, and URL                                                 | Response schema, `translation_required = true`, exact token preservation                                                            | Proposed gap: Japanese, emoji, release metadata                     |
| `C-HI-01` | Codex          | raw text        | Hindi-English code-mixed developer instruction                          | `kal PR #482 merge mat करना; tests flaky हैं, पहले uv run pytest tests/test_translate.py -q चलाओ और फिर deploy_notes.md update करो.` | Translate Hindi/Hinglish into English while preserving PR number, command, file path, and imperative intent                                                                   | Response schema, `translation_required = true`, command/path preservation, semantic adequacy                                        | Proposed gap: code-mixed Indic text                                 |
| `C-ES-01` | Codex          | structured JSON | Spanish with quoted text, handle, URL, and ambiguity                    | `@maria dijo: "No traduzcas el endpoint /v1/chat/completions"; revisa https://api.example.dev antes del viernes.`                    | Translate Spanish into English while preserving quote boundaries, handle, endpoint, URL, and deadline                                                                         | Response schema, `translation_required = true`, quoted code preservation, semantic adequacy                                         | Proposed gap: quoted don't-translate instruction inside source text |

- Reviewed and approved.

✅ **8B: Codex model and config comparison matrix**

- Propose exactly three Codex named callers to translate every reviewed smoke-test case.
- Do literature research before finalizing candidates, using current official model docs/pricing and credible translation-quality evidence where available.
- Optimize for highly reliable translations at the lowest practical cost.
- Research notes:
  - OpenAI model docs list `gpt-5.5` as the flagship model for complex reasoning/coding, with `gpt-5.4-mini` and `gpt-5.4-nano` recommended when optimizing for latency and cost.
  - OpenAI model docs say latest models support multilingual capabilities.
  - `gpt-5.4-mini` is documented as available in API, Codex, and ChatGPT, with lower Codex quota usage than full GPT-5.4.
  - Multilingual benchmark literature cautions that multilingual quality varies by language and task; this supports measuring our actual translation cases instead of assuming model size alone determines quality.
- Research sources to cite in the final 8B table:
  - OpenAI Models: `https://developers.openai.com/api/docs/models`
  - GPT-5.5 model pricing: `https://developers.openai.com/api/docs/models/gpt-5.5`
  - GPT-5.4 mini/nano launch notes: `https://openai.com/index/introducing-gpt-5-4-mini-and-nano/`
  - WMT25 MIST multilingual benchmark: `https://www2.statmt.org/wmt25/pdf/2025.wmt-1.24.pdf`
  - BenchMAX multilingual benchmark: `https://aclanthology.org/2025.findings-emnlp.909/`
- Use these three different Codex model candidates unless local Codex availability or Zeph guidance rules one out:
  - `translator_codex_gpt_54_mini`: low-cost baseline, `model = gpt-5.4-mini`, low reasoning, low verbosity
  - `translator_codex_gpt_54`: mid-tier reliability candidate, `model = gpt-5.4`, low reasoning, medium verbosity
  - `translator_codex_gpt_55`: frontier reliability candidate, `model = gpt-5.5`, low reasoning, medium verbosity
- Do not use `gpt-5.4-nano` for the initial Codex CLI matrix unless research confirms it is available in Codex and Zeph wants a cheaper fourth/alternate candidate.
- For each named caller, capture:
  - model
  - `model_reasoning_effort`
  - `model_verbosity`
  - prompt policy: checked-in `llm_callers.NAME.prompt` template or a reviewed temporary prompt variant
  - API-equivalent cost formula, even when the smoke run uses a subscription-backed Codex CLI session
  - source citations or notes for model availability and price
  - expected runtime class
- Cost formula conventions:
  - use retained token usage from the live smoke response
  - compute API-equivalent cost as `(input_tokens * input_price + cached_input_tokens * cached_input_price + output_tokens * output_price) / 1_000_000`
  - if reasoning tokens are reported separately, treat them as included in output tokens unless official pricing docs state otherwise
  - if cached input is unavailable, use `0` cached input tokens and all input as regular input
- Include the model/config matrix directly in this TODO before implementation, using this shape:

| Caller                         | Model          | Reasoning Effort | Verbosity | Prompt Policy                | Purpose                            | Cost                                                            | Runtime Class |
| ------------------------------ | -------------- | ---------------- | --------- | ---------------------------- | ---------------------------------- | --------------------------------------------------------------- | ------------- |
| `translator_codex_gpt_54_mini` | `gpt-5.4-mini` | `low`            | `low`     | checked-in translator prompt | low-cost baseline                  | `(input * $0.75 + cached_input * $0.075 + output * $4.50) / 1M` | Faster        |
| `translator_codex_gpt_54`      | `gpt-5.4`      | `low`            | `medium`  | checked-in translator prompt | mid-tier reliability/cost tradeoff | `(input * $2.50 + cached_input * $0.25 + output * $15.00) / 1M` | Fast          |
| `translator_codex_gpt_55`      | `gpt-5.5`      | `low`            | `medium`  | checked-in translator prompt | frontier reliability baseline      | `(input * $5.00 + cached_input * $0.50 + output * $30.00) / 1M` | Fast          |

- Reviewed and approved.

✅ **8C: Output retention and evaluator matrix design**

- Retain live smoke artifacts under `tmp/translate-smoke/{run_id}/`.
- Use `run_id = YYYYMMDD-HHMMSS-{short_sha_or_nogit}`.
- Do not commit retained smoke artifacts by default.
- Retain, per run:
  - case id
  - named caller
  - source input
  - full translation request JSON
  - full translation response JSON
  - rendered translated text
  - warnings
  - token/timing usage
  - command/config metadata with secrets redacted
- Artifact layout:
  - `manifest.json`: run id, git commit, command, environment opt-ins, selected cases, selected callers, redacted config summary
  - `cases/{case_id}/source.txt`: exact source input
  - `cases/{case_id}/expected.md`: expected translation intent and preservation requirements
  - `runs/{case_id}/{caller}/request.json`: full translation request JSON
  - `runs/{case_id}/{caller}/response.json`: full translation response JSON
  - `runs/{case_id}/{caller}/translated.txt`: rendered translated text or original text for English pass-through
  - `runs/{case_id}/{caller}/usage.json`: token/timing usage and computed API-equivalent cost
  - `runs/{case_id}/{caller}/stderr.txt`: redacted stderr/warnings when present
  - `evaluation/evaluator-input.jsonl`: one JSON object per retained translation output
  - `evaluation/evaluator-output.md`: evaluator scoring matrix and notes
- `evaluator-input.jsonl` object fields:
  - `case_id`: reviewed smoke case id, for example `Z-CN-01`
  - `caller`: reviewed named caller, for example `translator_codex_gpt_54_mini`
  - `source_text`: exact source input
  - `expected_translation_intent`: reviewed case intent from 8A
  - `preservation_requirements`: reviewed URLs, commands, handles, names, numbers, and quoted strings to preserve
  - `translation_required`: boolean from translation response
  - `translated_text`: rendered translated text, or original text when English pass-through was expected
  - `response_warnings`: response-level and block-level warnings
  - `usage`: full `usage.json` object
  - `response_path`: relative path to retained `response.json`
- `usage.json` cost fields:
  - `input_tokens`
  - `cached_input_tokens`
  - `output_tokens`
  - `reasoning_tokens`
  - `input_price_per_million`
  - `cached_input_price_per_million`
  - `output_price_per_million`
  - `api_equivalent_cost_usd`
- Define an evaluator workflow using Codex ChatGPT 5.5 Extra High effort.
- Evaluator prompt must instruct the evaluator to score fidelity to the source, not whether it agrees with source claims or sentiment.
- Evaluator prompt must preserve offensive/political text as translation fidelity criteria, while flagging unnecessary additions or sanitization.
- The evaluator grades translations into an output matrix with at least:
  - case id
  - named caller
  - actual API-equivalent cost computed from the model/config matrix formula and retained usage
  - adequacy score
  - fluency score
  - preservation score for URLs/code/handles/names
  - instruction-following/schema score
  - warnings or failure notes
  - preferred output for the case
- Score scale:
  - `5`: excellent
  - `4`: minor issues
  - `3`: usable with noticeable issues
  - `2`: major issues
  - `1`: unusable or wrong
- Preferred output rule:
  - mark exactly one preferred caller per case unless all outputs are unusable
  - prefer the lowest-cost output among tied quality scores
  - explain ties or no-preference outcomes in evaluator notes
- Include the evaluator output matrix template directly in this TODO before implementation, using this shape:

| Case ID     | Caller     | Cost                                         | Adequacy    | Fluency     | Preservation | Instruction Following | Total              | Preferred?                                                                    | Warnings / Failures                        | Evaluator Notes                                               |
| ----------- | ---------- | -------------------------------------------- | ----------- | ----------- | ------------ | --------------------- | ------------------ | ----------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------- |
| `{case_id}` | `{caller}` | `$api_equivalent_cost_usd` from `usage.json` | integer 1-5 | integer 1-5 | integer 1-5  | integer 1-5           | sum of four scores | `yes` for exactly one caller per case unless all are unusable; otherwise `no` | concrete warning/failure summary or `none` | concise rationale with any important source-fidelity concerns |

- Reviewed and approved.

✅ **8D: Offline-safe pytest opt-in plumbing**

- Add a `live_codex_cli` pytest marker for Codex CLI live smoke tests.
- Register the marker in `pyproject.toml` so `--strict-markers` accepts it.
- Add a collection-time skip rule in `tests/conftest.py`:
  - tests marked `live_codex_cli` are skipped unless `CURIO_LIVE_CODEX_CLI_TESTS=1`
  - skipped collection must not import runtime secrets, load real config files, touch network, call `codex`, or instantiate subprocess runners
- Add a helper function for opt-in parsing with exact truth semantics:
  - enabled only when the environment value is exactly `1`
  - unset, empty, `0`, `true`, `yes`, and any other value are disabled
- Use skip reason: `set CURIO_LIVE_CODEX_CLI_TESTS=1 to run Codex CLI live smoke tests`
- Add offline tests for:
  - marker is registered
  - unset env skips marked tests
  - `CURIO_LIVE_CODEX_CLI_TESTS=1` allows marked tests to run
  - non-`1` values skip marked tests
  - unmarked tests are unaffected
- Keep live smoke tests outside default `make check`; default collection and test execution must remain auth-free and network-free.
- Added `live_codex_cli` pytest marker registration.
- Added `CURIO_LIVE_CODEX_CLI_TESTS=1` exact opt-in gate.
- Added collection-time skip rule in `tests/conftest.py`.
- Added offline tests for marker registration, skip behavior, opt-in behavior, non-`1` values, and unmarked tests.
- 🧪 Passed `make check` with 100% coverage.

✅ **8E: Codex CLI live smoke harness helpers**

- Add small helpers for loading explicit runtime config, selecting `llm_callers.NAME`, constructing CLI/service calls, normalizing Codex CLI outputs, retaining evaluator-ready outputs, and reporting actionable skip/failure messages.
- Keep helpers narrow and keep Codex-specific behavior inside `curio.llm_caller`.
- Treat config loading as part of every live smoke path, including explicit `--llm-caller`, because prompt templates are resolved from the selected named caller.
- Ensure failures redact secrets and do not dump request auth/config internals.
- Prefer bounded timeouts and one model call per smoke case per named caller unless the reviewed matrix says otherwise.
- Cover helper behavior with offline fake Codex-runner tests.
- Kept live-smoke helpers test-only under `tests/live_smoke_helpers.py`; no production helper module was added.
- Added offline fake-client/helper tests for config selection, Codex-only validation, service construction, output rendering, API-equivalent cost math, redacted caller summaries, evaluator input records, and retained artifact writing.
- 🧪 Passed `make check` with 100% coverage.

✅ **8F: Codex CLI live smoke tests**

- Add skipped-by-default Codex CLI smoke tests from the reviewed matrix.
- Verify every reviewed smoke-test case can run against each reviewed Codex named caller.
- Verify `curio translate --llm-caller translator_codex_gpt_54_mini` works through explicit named config selection.
- Verify `curio translate` works through configured `translate.llm_caller`.
- Verify the checked-in `config.example.codex_cli.json` prompt templates are loaded through `llm_callers.NAME.prompt` and still produce valid translation response JSON.
- If the reviewed matrix includes prompt-variant coverage, verify a temporary Codex config with modified `llm_callers.NAME.prompt` still produces valid translation response JSON.
- Check both CLI behavior and translation response JSON where appropriate.
- Retain inputs and outputs in the reviewed retention format for evaluator scoring.
- Fail with clear operator guidance when `codex` is missing, login is absent, config is missing, or the live opt-in is incomplete.
- Keep default `make check` independent of a real `codex` binary or `codex login`.
- Added `translator_codex_gpt_54` to `config.example.codex_cli.json` so the checked-in config matches the reviewed three-caller matrix.
- Added `tests/test_translate_live_smoke.py` with `live_codex_cli` marked tests covering:
  - all reviewed smoke cases across `translator_codex_gpt_54_mini`, `translator_codex_gpt_54`, and `translator_codex_gpt_55`
  - retained evaluator-ready artifacts under `tmp/translate-smoke/{run_id}/`
  - configured `translate.llm_caller` CLI selection
  - explicit `--llm-caller translator_codex_gpt_54_mini` CLI selection
- Live run command:
  - `make translate-smoke`
- Live test collection command:
  - `make translate-smoke-collect`
- Default `make check` collects the live tests but skips them unless explicitly opted in.
- 🧪 Passed `make check` with 187 passed, 31 skipped, and 100% coverage.

✅ **8G: Evaluator grading pass**

- Run the evaluator only after live smoke outputs have been retained.
- Use Codex ChatGPT 5.5 Extra High effort as the evaluator.
- Feed the evaluator retained source inputs, expected translation intent, translated outputs, warnings, and relevant metadata.
- Produce the reviewed evaluator output matrix.
- Keep evaluator results separate from pass/fail smoke assertions unless Zeph explicitly promotes a score threshold into the gate.
- Ran evaluator against retained smoke run `tmp/translate-smoke/20260426-060103-22de460b22c0`.
- Saved evaluator artifacts:
  - `evaluation/evaluator-input.jsonl`
  - `evaluation/evaluator-payload.json`
  - `evaluation/evaluator-prompt.md`
  - `evaluation/evaluator-run.jsonl`
  - `evaluation/evaluator-output.md`
- Added reusable evaluator tooling in `tests/live_smoke_evaluator.py` so future runs retain the evaluator code and prompt template in the codebase.
- Added offline tests for evaluator payload enrichment, prompt generation, Codex command construction, latest-run resolution, and invalid retained input handling.
- Added Makefile target:
  - `make translate-smoke-evaluate`
  - optionally set `TRANSLATE_SMOKE_RUN=tmp/translate-smoke/<run_id>`
- Published durable report artifacts under `reports/translate-smoke/20260426-060103-22de460b22c0/`, including evaluator output, prompt, payload, retained cases, retained per-case/caller run outputs, CLI outputs, and a human-readable translations rollup.
- Added `make translate-smoke-report` to republish report artifacts for a retained smoke run without rerunning the evaluator.
- 🧪 Passed `make check` with 196 passed, 31 skipped, and 100% coverage.

✅ **8H: Live smoke test operator docs**

- Document the reviewed smoke-test matrix.
- Document the reviewed model/config matrix.
- Document where retained inputs, outputs, and evaluator matrices live.
- Document how to run the Codex CLI live smoke tests.
- Include required `llm_callers.NAME` config examples, checked-in `llm_callers.NAME.prompt` template behavior, optional prompt-variant examples, Codex auth prerequisites, expected environment variables, timeouts, runtime notes, and common failure messages.
- Document how to run the Codex ChatGPT 5.5 Extra High effort evaluator pass.
- Cross-link `AUTHENTICATION.md`, `USAGE.md`, and `TRANSLATE.md`.
- Added `SMOKE-TESTS.md` with the live smoke matrix, model/config matrix, commands, artifact locations, Codex prerequisites, prompt-template notes, common failures, and evaluator workflow.
- Added `reports/translate-smoke/20260426-060103-22de460b22c0/UPSHOT.md` recommending `translator_codex_gpt_54_mini` as the default translation caller and `translator_codex_gpt_54` as the escalation caller, with quantified API-equivalent cost comparisons.
- Linked `SMOKE-TESTS.md` and the current report `UPSHOT.md` from `README.md`.
- Added a live smoke test pointer in `USAGE.md`.
- Tightened `make translate-smoke-report` so durable reports default to human-facing docs only; raw machine/debug artifacts require `--include-raw-artifacts` through the evaluator script.
- 🧪 Passed `make check` with 197 passed, 31 skipped, and 100% coverage.

🟡 **8I: Final smoke harness review**

- Run `make check` with live tests skipped.
- If local Codex CLI auth is available and explicitly opted in, run the reviewed live smoke subset.
- If retained live outputs exist, run the evaluator pass and record the output matrix.
- Confirm no secrets appear in stdout, stderr, pytest failure output, or exceptions.
- Confirm retained inputs/outputs and evaluator matrices redact secrets and keep enough context for later scoring review.
- Confirm docs match actual command names, config paths, markers, and environment variables.
- Mark checkpoint 8 complete only after offline checks pass and any manually run live checks are recorded.
- 🧪 Gate: `make check`, 100% coverage, then pause.

## PUNT

🔒 ⬜ **OpenAI API live smoke tests**

- Punt all OpenAI API client smoke-test work out of the current session.
- Later, decide whether to add OpenAI API cases to the smoke-test matrix.
- Later, add skipped-by-default OpenAI API smoke tests behind an explicit opt-in such as `CURIO_LIVE_OPENAI_API_TESTS=1`.
- Later, verify `curio translate --llm-caller translator_openai_gpt_54_mini_cold` works through explicit config and Keychain-backed API key lookup.
- Later, check both CLI behavior and translation response JSON where appropriate.
- Later, fail with clear operator guidance when config, Keychain secret, model, network, or live opt-in is missing.
- Later, keep default `make check` independent of network access or real API keys.
- Later, update live smoke test docs with OpenAI API prerequisites, expected cost/network behavior, and troubleshooting.

## Hard Rules

- 🛑 Pause after every major or sub-checkpoint.
- 🛑 Do not move forward without user approval.
- 🧪 Every checkpoint must pass `make check` with 100% coverage.
- 🧪 Use `uv` for Python execution.
- 🧩 Keep provider-specific behavior out of `curio.translate`.
- 🔐 Treat provider auth as configuration, not workflow capability.
