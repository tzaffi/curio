# Curio CLI

## Purpose

Define the normative v1 command-line shape for Curio.

This document is normative for:

- the top-level `curio` module command
- the required subcommand names
- the standalone `translate` command behavior
- stubs for workflows that are not fully specified yet
- operator-facing output and exit-code expectations

This document is not the place to define:

- translation quality rules or JSON payloads
- provider adapter behavior
- Google Sheets or Drive persistence
- exact prompt wording

Those belong in [TRANSLATE.md](TRANSLATE.md), [LLM-CALLER.md](LLM-CALLER.md), [SCHEMA.md](SCHEMA.md), [JSON-PAYLOAD.md](JSON-PAYLOAD.md), and prompt files.

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
- `curate`
  Main Curio workflow over `downloads` rows. Stubbed here; detailed implementation remains future work.
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

Required v1 flags:

- `--input-file PATH`
  Read one raw text block from a UTF-8 text file.
- `--input-json PATH`
  Read the structured JSON request defined in [TRANSLATE.md](TRANSLATE.md).
- `--json`
  Print the full structured translation response.
- `--output PATH`
  Write command output to a file instead of stdout.
- `--source-language LANG`
  Optional source-language hint.
- `--target-language LANG`
  Target language. V1 accepts only `en`.
- `--english-confidence-threshold FLOAT`
  Minimum model confidence for treating a block as English without translation. Defaults to `0.90`.
- `--provider PROVIDER`
  LLM provider override, such as `codex_cli` or `openai_api`. Defaults to `codex_cli`.
- `--model MODEL`
  Provider model override.
- `--timeout-seconds SECONDS`
  Provider-call wall-clock timeout. Defaults to `300`.

JSON formatting flags such as `--pretty` and `--compact` are out of scope for v1.

Detected source-language values may still use more specific English tags such as `en-US` or `en-GB`.

### Output Modes

For raw single-block input without `--json`, stdout should contain only the translated English text plus a trailing newline.

For structured input or when `--json` is set, stdout should contain the full translation response JSON defined in [TRANSLATE.md](TRANSLATE.md).

Warnings and diagnostics belong on stderr unless `--json` is active. In JSON mode, warnings belong in the response object.

### Exit Codes

Recommended v1 exit codes:

- `0`
  Success.
- `1`
  Runtime failure, including provider errors and invalid provider output.
- `2`
  CLI usage error.

Typer may handle usage errors directly, but tests should assert user-visible behavior rather than Typer internals.

## `curate`

The `curate` subcommand is the main Curio workflow.

Reserved form:

```text
uv run python -m curio curate [FLAGS]
```

This command will eventually:

- read candidate rows from the configured `downloads` sheet
- assemble dossiers
- call translation when needed
- call evaluation
- persist accepted results to Sheets and Drive
- rebuild or update `catalog`

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
- `translate` rejects ambiguous input modes
- `translate` can select either `openai_api` or `codex_cli` through the shared LLM caller
- future subcommand names are reserved without forcing their full behavior into the translate implementation
