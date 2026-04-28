# Smoke Tests

The translation smoke suite is an opt-in live test harness for the Codex CLI translation path. It is intentionally outside the default `make check` execution path because it requires a real `codex` binary, ChatGPT login, network access, and model quota.

## Scope

Active scope is Codex CLI only. OpenAI API live smoke tests are punted and should stay behind a separate future opt-in.

The live matrix is:

| Case | Scenario |
| --- | --- |
| `Z-CN-01` | Chinese Hermes WebUI thread; URLs, handle, SSH command |
| `Z-CN-02` | Chinese Agent Skills explainer; slash commands and tool names |
| `Z-EN-01` | English pass-through baseline |
| `Z-KO-01` | Korean local LLM setup; mixed English model/tool tokens |
| `Z-AR-01` | Arabic RTL, colloquial AI hardware text, English technical terms |
| `Z-HE-01` | Hebrew political/security statement |
| `Z-HE-02` | Hebrew graphic/profane invective |
| `C-JA-01` | Japanese release note; emoji, hashtag, URL, code-like tokens |
| `C-HI-01` | Hindi/Hinglish developer instruction; command and filename |
| `C-ES-01` | Spanish quoted endpoint instruction; handle and URL |

Each case is run against:

| Caller | Model | Reasoning | Verbosity | Purpose |
| --- | --- | --- | --- | --- |
| `translator_codex_gpt_54_mini` | `gpt-5.4-mini` | `low` | `low` | low-cost default candidate |
| `translator_codex_gpt_54` | `gpt-5.4` | `low` | `medium` | reliability fallback candidate |
| `translator_codex_gpt_55` | `gpt-5.5` | `low` | default | frontier reliability baseline |

The evaluator is Codex `gpt-5.5` with `model_reasoning_effort="xhigh"`.

## Prerequisites

Read [AUTHENTICATION.md](AUTHENTICATION.md), [USAGE.md](USAGE.md), and [TRANSLATE.md](TRANSLATE.md) first.

Required local state:

- `codex` CLI installed and on `PATH`
- Codex CLI logged in through ChatGPT auth
- `~/.codex/config.toml` configured as described in [AUTHENTICATION.md](AUTHENTICATION.md)
- network access and enough model quota
- checked-in `config.example.codex_cli.json` present

The checked-in Codex config defines named callers under `llm_callers.NAME`; live tests select those names and verify prompt templates under `llm_callers.NAME.prompt`. For one-off prompt experiments, use a temporary config file and keep the default report separate from checked-in reports.

## Commands

List live smoke tests without running them:

```bash
make translate-smoke-collect
```

Run the live smoke matrix:

```bash
make translate-smoke
```

This expands to:

```bash
CURIO_LIVE_CODEX_CLI_TESTS=1 uv run pytest -m live_codex_cli -s --no-cov
```

The environment value must be exactly `1`; unset, empty, `0`, `true`, and `yes` all skip live tests. Do not omit `--no-cov` when running only the live marker directly; the repo’s coverage gate expects the full offline test suite.

Run the evaluator for the latest retained run:

```bash
make translate-smoke-evaluate
```

Run the evaluator for a specific retained run:

```bash
make translate-smoke-evaluate TRANSLATE_SMOKE_RUN=tmp/translate-smoke/<run_id>
```

Publish human-facing report files without rerunning the evaluator:

```bash
make translate-smoke-report TRANSLATE_SMOKE_RUN=tmp/translate-smoke/<run_id>
```

## Artifacts

Raw retained artifacts live under:

```text
tmp/translate-smoke/{run_id}/
```

That directory is for local forensic debugging. It may contain request JSON, response JSON, token usage, evaluator prompt/payload, CLI stdout, and per-case source fixtures.

Durable human reports live under:

```text
reports/translate-smoke/{run_id}/
```

Keep these files for human review:

- `UPSHOT.md`: caller recommendation, cost summary, and escalation policy
- `evaluator-output.md`: evaluator scoring matrix and per-case preference notes
- `translations.md`: source text, expected intent, preservation requirements, cost, and translated text for each case/caller

The current completed report is indexed from [reports/README.md](reports/README.md).

## Common Failures

- `codex_cli executable not found`: install Codex CLI or fix `PATH`.
- Codex auth/login failure: run Codex login setup and verify `cli_auth_credentials_store = "keyring"`.
- `reasoning.effort 'minimal'` tool rejection: use `low` or higher for these live callers.
- `invalid_json_schema`: Codex response-format schema support is narrower than local JSON Schema validation. The provider client strips unsupported handoff keywords while preserving local validation against the original schema.
- timeout: rerun a smaller subset or increase the selected caller timeout in a temporary config.
- coverage failure when running `pytest -m live_codex_cli`: use `make translate-smoke` or include `--no-cov`.

## Result Policy

Live smoke pass/fail checks verify schema validity, caller selection,
pass-through behavior, and artifact retention. Translation and textification
quality decisions come from evaluator reports, not from pytest assertions,
unless a future checkpoint promotes an evaluator threshold into the gate.

## Textify Smoke Tests

The textify smoke suite is also opt-in and Codex CLI-only for v1. It is skipped
from default `make check`.

The active Codex CLI caller matrix is:

| Caller | Model | Purpose |
| --- | --- | --- |
| `textifier_codex_gpt_54_mini` | `gpt-5.4-mini` | likely default balance |
| `textifier_codex_gpt_53_codex` | `gpt-5.3-codex` | Codex-optimized cost/quality comparison |
| `textifier_codex_gpt_55` | `gpt-5.5` | frontier reliability baseline |

`gpt-5.4-nano` is not included because Codex CLI rejects it when using
ChatGPT auth.

List live textify smoke tests without running them:

```bash
make textify-smoke-collect
```

Run the live textify matrix:

```bash
make textify-smoke
```

This expands to:

```bash
CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS=1 uv run pytest -m live_codex_cli_textify -s --no-cov
```

Prepare the evaluator prompt and run the evaluator for the latest retained run:

```bash
make textify-smoke-evaluate
```

Publish report files without rerunning the evaluator:

```bash
make textify-smoke-report TEXTIFY_SMOKE_RUN=tmp/textify-smoke/<run_id>
```

Raw retained artifacts live under:

```text
tmp/textify-smoke/{run_id}/
```

Durable human reports live under:

```text
reports/textify-smoke/{run_id}/
```

The textify evaluator should judge OCR/text fidelity, source-language
preservation, document structure, suggested filenames/extensions/paths,
multi-file handling, warning quality, and cost. It should produce the final
model recommendation after live smoke data exists.

The current textify recommendation is recorded in
[reports/textify-smoke/20260428-132551-09c3fa3c8f75/UPSHOT.md](reports/textify-smoke/20260428-132551-09c3fa3c8f75/UPSHOT.md).
