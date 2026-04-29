# Curio CLI

## Purpose

Define the normative v1 command-line shape for Curio.

This document is normative for:

- the top-level `curio` module command
- the required subcommand names
- the standalone `translate` command behavior
- the standalone `textify` command behavior
- the reserved `pipeline` command group
- stubs for workflows that are not fully specified yet
- operator-facing output and exit-code expectations

This document is not the place to define:

- translation or textification quality rules or JSON payloads
- provider adapter behavior
- Google Sheets or Drive persistence
- exact prompt wording

Those belong in [PIPELINE.md](PIPELINE.md), [TRANSLATE.md](TRANSLATE.md), [TEXTIFY.md](TEXTIFY.md), [LLM-CALLER.md](LLM-CALLER.md), [SCHEMA.md](SCHEMA.md), [JSON-PAYLOAD.md](JSON-PAYLOAD.md), and prompt files.

## Design Principles

The v1 CLI should follow these rules:

- The module entrypoint is `uv run python -m curio`.
- The installed console script may be `curio`, but module execution is the normative development path.
- The root command prints help when no subcommand is provided.
- Subcommands are explicit verbs.
- Machine-readable workflows offer JSON output.
- Human-readable defaults are compact and safe for terminal use.
- CLI errors are concise and exit non-zero.
- Implementation should follow `iMsgX` and `forwarder`: Typer commands, type-annotated options, small command handlers, and logic pushed into testable modules.

## Codex CLI Prerequisite

Curio's default v1 LLM provider is the Codex CLI.

Operators should install the standalone `codex` command with:

```text
npm i -g @openai/codex
```

After installation, `codex` should be available on the shell `PATH`.

The Codex desktop app may also bundle a `codex` binary inside the application bundle. Curio may mention that path in diagnostics, but app-bundled paths are not the normative installation method.

## Required Subcommands

V1 reserves these subcommands:

- `translate`
  Standalone text translation. Fully specified in v1.
- `textify`
  Standalone media-to-text extraction. Fully specified in v1.
- `pipeline`
  Processor-led Curio workflow over `downloads` rows. Reserved here and
  specified in [PIPELINE.md](PIPELINE.md).
- `curate`
  Human-facing curation workflow. It may wrap `pipeline run` plus catalog
  refresh and review affordances.
- `bootstrap`
  Label-registry bootstrap workflow. Normative behavior is defined in [BOOTSTRAP.md](BOOTSTRAP.md), but the CLI flags remain future work.
- `schema`
  Future schema validation and inspection helper.
- `doctor`
  Future local configuration and provider-auth diagnostic helper.

## Root Command

The root command is:

```text
uv run python -m curio
```

When invoked without a subcommand, it should print help and exit successfully.

## `translate`

The `translate` subcommand translates text into English.

Primary examples:

```text
uv run python -m curio translate "今日は新しいモデルを公開します。"
printf '%s\n' '今日は新しいモデルを公開します。' | uv run python -m curio translate
uv run python -m curio translate --input-file note.txt
uv run python -m curio translate --input-json request.json --json
```

### Input Modes

`translate` must support these input modes:

- raw text as the positional argument
- raw text from stdin
- raw text from `--input-file`
- structured translation request JSON from `--input-json`

Exactly one input mode should be used.

If more than one input mode is provided, the command must fail with a usage error.

If no input mode is provided and stdin is not piped, the command must fail with a usage error rather than hanging.

### Core Flags

V1 flags:

- `--input-file PATH`
  Read one raw text block from a UTF-8 text file.
- `--input-json PATH`
  Read the structured JSON request defined in [TRANSLATE.md](TRANSLATE.md).
- `--json`
  Print the full structured translation response.
- `--suppress-warnings`
  Do not print translation warnings to stderr in non-JSON mode.
- `--stats`
  Print provider, model, token usage, wall time, and cost-estimate metadata to stderr in non-JSON mode.
- `--output PATH`
  Write command output to a file instead of stdout.
- `--source-language LANG`
  Optional source-language hint.
- `--target-language LANG`
  Target language. V1 accepts only `en`.
- `--english-confidence-threshold FLOAT`
  Minimum model confidence for treating a block as English without translation. Defaults to `0.90`.
- `--llm-caller NAME`
  Override the named LLM caller for this run, such as `translator_codex_gpt_55` or `translator_openai_gpt_54_mini_cold`.

LLM caller resolution precedence is CLI `--llm-caller`, then structured JSON
`llm_caller`, then `config.json` `translate.llm_caller`. If none is available,
the command must fail with a usage error.

JSON formatting flags such as `--pretty` and `--compact` are out of scope for v1.

Detected source-language values may still use more specific English tags such as `en-US` or `en-GB`.

### Output Modes

For raw single-block input without `--json`, stdout should contain only the translated English text plus a trailing newline.

For structured input or when `--json` is set, stdout should contain the full translation response JSON defined in [TRANSLATE.md](TRANSLATE.md).

Warnings and diagnostics belong on stderr unless `--json` is active. In JSON mode, warnings belong in the response object.
In non-JSON mode, warnings should be visibly prefixed:

```text
[WARNINGS: warning text]
```

When terminal color is supported, warning lines should be red. `--suppress-warnings`
suppresses this human stderr output only; it must not remove warnings from JSON
responses. `--stats` prints usage and cost metadata to stderr and must not add
metadata to plain translation stdout.

### Exit Codes

Recommended v1 exit codes:

- `0`
  Success.
- `1`
  Runtime failure, including provider errors and invalid provider output.
- `2`
  CLI usage error.

Typer may handle usage errors directly, but tests should assert user-visible behavior rather than Typer internals.

## `textify`

The `textify` subcommand converts one local source artifact, or a structured
single-source textify request JSON file, into source-language text.

Primary examples:

```text
uv run python -m curio textify screenshot.png
uv run python -m curio textify --input-file screenshot.png
uv run python -m curio textify --input-json textify-request.json --json
uv run python -m curio textify screenshot.png --preferred-output-format markdown --stats
```

Input modes:

- local artifact path as the positional argument
- local artifact path from `--input-file`
- structured single-source textify request JSON from `--input-json`

Exactly one input mode should be used.

Core flags:

- `--input-file PATH`
  Read a local media artifact path from an option instead of the positional argument.
- `--input-json PATH`
  Read the structured JSON request defined in [TEXTIFY.md](TEXTIFY.md).
- `--json`
  Print the full structured textify response.
- `--suppress-warnings`
  Do not print textify warnings to stderr in non-JSON mode.
- `--stats`
  Print provider, model, usage, wall time, and cost-estimate metadata to stderr in non-JSON mode.
- `--output PATH`
  Write command output to a file instead of stdout.
- `--mime-type TYPE`
  Optional MIME type override for artifact path input.
- `--source-language LANG`
  Optional source-language hint for artifact path input.
- `--preferred-output-format auto|markdown|txt`
  Output format hint. `auto` is the default.
- `--llm-caller NAME`
  Override the named LLM caller for this run, such as `textifier_codex_gpt_54_mini`.

LLM caller resolution precedence is CLI `--llm-caller`, structured JSON
`llm_caller`, then `config.json` `textify.llm_caller`. If the source is
deterministically skipped or unsupported, no LLM caller is required.

For a skipped text-media source without `--json`, stderr contains a compact
warning and stdout is empty. For one converted suggested file without `--json`,
stdout contains that file's text plus a trailing newline. For structured input,
`--json`, or multiple/no suggested files, stdout contains the full textify
response JSON.

## `pipeline`

The `pipeline` command group is the processor-led Curio workflow defined in
[PIPELINE.md](PIPELINE.md).

Reserved forms:

```text
uv run python -m curio pipeline run [OPTIONS]
uv run python -m curio pipeline run-stage STAGE [OPTIONS]
uv run python -m curio pipeline doctor [OPTIONS]
```

Reserved stages:

- `textify`
- `translate`
- `dossier` (later; punted from current implementation pass)
- `evaluate` (later; punted from current implementation pass)

V1 pipeline commands are synchronous. They should append compact rows to
processor-owned tabs, persist artifacts through the configured artifact store,
and stop at the requested limit or first unrecoverable runtime failure.

Append-capable commands are intentionally narrow:

- `--limit N`
- `--persist`

`pipeline run` and `pipeline run-stage STAGE` may append only for next-available
limited sweeps. `--limit` defaults to `10`, so `pipeline run-stage textify
--persist` means "append rows for the next 10 textify candidates." Without
`--persist`, the same next-available sweep must fail rather than mutating
implicitly.

Targeted selectors are preview-only and must not be combined with `--persist`:

- `--start DATE_OR_DATETIME`
- `--end DATE_OR_DATETIME`
- `--source SOURCE`
- `--row N`
- `--from-row N`
- `--to-row N`
- `--json`

`--start` and `--end` are intended to filter upstream `downloads` rows by X Date
using the same date-only and ISO datetime style as iMsgX. `--row`,
`--from-row`, and `--to-row` refer only to upstream downloads input row
numbers. They never select output row positions; processor tabs are append-only
and write to the first available row.

There is no source runner. `pipeline run` means the whole pipeline, and
`pipeline run-stage` means one processor. Source selectors are only meaningful
inside an explicit stage or diagnostic command. `pipeline doctor` is a
non-mutating diagnostic command and may accept targeted selectors.

Current implementation status: the option surface is reserved and visible in
help. Actual pipeline execution remains blocked on the Google Sheets-backed
pipeline store, so commands fail clearly rather than touching live Google
Sheets.

## `curate`

The `curate` subcommand is the human-facing Curio curation workflow.

Reserved form:

```text
uv run python -m curio curate [FLAGS]
```

This command may eventually wrap `pipeline run` and then:

- rebuild or update `catalog`
- surface accepted evaluations for review
- support label-registry maintenance around proposals

Detailed flags are intentionally not specified in this document yet.

## `bootstrap`

The `bootstrap` subcommand is reserved for the workflow defined in [BOOTSTRAP.md](BOOTSTRAP.md).

Reserved form:

```text
uv run python -m curio bootstrap [FLAGS]
```

Detailed flags are intentionally not specified in this document yet.

## `schema`

The `schema` subcommand is reserved for validating local JSON payloads and printing schema metadata.

Reserved form:

```text
uv run python -m curio schema [FLAGS]
```

Detailed flags are intentionally not specified in this document yet.

## `doctor`

The `doctor` subcommand is reserved for local diagnostics.

Reserved form:

```text
uv run python -m curio doctor [FLAGS]
```

It should eventually check:

- local config files
- Google auth prerequisites
- OpenAI API auth prerequisites
- Codex CLI availability and login state
- write access to configured output locations

Detailed flags are intentionally not specified in this document yet.

## Configuration Precedence

When implemented, CLI configuration should resolve in this order:

1. explicit CLI flags
2. environment variables
3. Curio config file
4. safe built-in defaults

The CLI must not require users to pass provider credentials directly as command-line flag values.

## Acceptance Scenarios

The CLI spec is satisfied only if all of the following are true:

- `uv run python -m curio` prints help
- `uv run python -m curio translate "bonjour"` prints an English translation by default
- `uv run python -m curio translate --json "bonjour"` prints a structured translation response
- `uv run python -m curio textify --json screenshot.png` prints a structured textify response
- `translate` rejects ambiguous input modes
- `textify` rejects ambiguous input modes
- `translate` can select either `openai_api` or `codex_cli` through the shared LLM caller
- `pipeline` is reserved as a command group without forcing full pipeline behavior into standalone textify or translate commands
- future subcommand names are reserved without forcing their full behavior into the translate implementation
