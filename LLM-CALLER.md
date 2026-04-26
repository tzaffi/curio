# Curio LLM Caller

## Purpose

Define the normative v1 boundary for calling large language models from Curio workflows.

This document is normative for:

- the provider-neutral request and response shape used by Curio modules
- the Python module boundary for `curio.llm_caller`
- provider client responsibilities
- usage and timing accounting
- the v1 provider set: Codex CLI and OpenAI API
- how unsupported provider capabilities fail

The machine-readable counterparts to this document are:

- [schemas/llm_request.schema.json](schemas/llm_request.schema.json)
- [schemas/llm_response.schema.json](schemas/llm_response.schema.json)

This document is not the place to define:

- translation-specific JSON contracts
- dossier assembly behavior
- Google Sheets or Drive persistence
- exact prompt wording for a workflow
- external provider pricing

Those belong in [TRANSLATE.md](TRANSLATE.md), [JSON-PAYLOAD.md](JSON-PAYLOAD.md), [SCHEMA.md](SCHEMA.md), prompt files, and operator docs.

## Design Principles

The v1 LLM caller should follow these rules:

- Curio modules depend on a small local protocol, not on a provider SDK.
- Provider-specific code belongs behind provider clients.
- The core request and response types are JSON-serializable without losing meaning.
- Structured output is requested through JSON Schema when the provider supports it.
- Unsupported required capabilities fail before a remote call is attempted.
- Token, metered-object, and timing accounting are recorded when available and explicitly `null` when unavailable.
- Provider raw responses are not part of the stable Curio contract.
- Provider-specific features may be exposed through capability flags, but Curio workflows must not silently require them.
- The code should match the style of `iMsgX` and `forwarder`: Python 3.12, Typer for CLIs, frozen slotted dataclasses for domain records, `StrEnum` for closed string sets, clear pure functions, narrow exceptions, and tests that exercise the public behavior.
- Unit tests should preserve the `iMsgX` and `forwarder` standard of `100%` coverage. Provider behavior should be tested with fakes and fixtures by default, not live network calls.

## Module Boundary

The implementation module should be named:

```text
curio.llm_caller
```

The public boundary should include:

- `LlmClient`
  A `Protocol` with one method, `complete(request: LlmRequest) -> LlmResponse`.
- `LlmRequest`
  Frozen slotted dataclass representing the provider-neutral request.
- `LlmResponse`
  Frozen slotted dataclass representing the provider-neutral response.
- `LlmUsage`
  Frozen slotted dataclass for token, metered-object, and timing data.
- concrete clients:
  - `CodexCliClient`
  - `OpenAiApiClient`

Curio workflows should accept an `LlmClient` dependency. They should not import provider SDKs, spawn provider CLIs, read provider auth files, or parse provider raw responses directly.

`LlmClient` is the workflow-facing abstraction. Named LLM caller choice happens at startup, configuration loading, or CLI parsing time. The selected provider-specific client is then injected into the workflow service. V1 must not silently route to a different caller when the selected caller fails.

## Named Caller Configs

V1 config uses named `llm_callers` plus workflow defaults such as
`translate.llm_caller`. Each named caller entry owns:

- `provider`: `codex_cli` or `openai_api`
- `model`
- `auth`
- `timeout_seconds`
- provider-specific tuning
- optional translator prompt overrides

Multiple entries may use the same provider with different models or tuning, such as `translator_codex_gpt_55`, `translator_codex_gpt_54_mini`, and `translator_openai_gpt_54_mini_cold`.

Translator prompt overrides live under the selected named caller:

```json
{
  "llm_callers": {
    "translator_codex_gpt_54_mini": {
      "prompt": {
        "instructions": "Return only JSON for {request_id}.",
        "user": "Request:\n{translation_request_json}\n\nSchema:\n{output_schema_json}"
      }
    }
  }
}
```

The supported template placeholders are `translation_request_json`,
`output_schema_json`, `request_id`, `target_language`, and
`english_confidence_threshold`.

Translation caller selection is resolved in this order:

1. CLI `--llm-caller`
2. structured JSON `llm_caller`
3. `config.json` `translate.llm_caller`

The resolved name is stored back onto the translation request before the
translation service builds the LLM request metadata.

Provider identifiers are:

- `codex_cli`
  Local subprocess calls to `codex exec`.
- `openai_api`
  Direct OpenAI API calls.

V1 must fully specify and unit-test both providers. Future providers may be added by implementing `LlmClient`, but they must declare capabilities explicitly before Curio workflows can depend on them.

## Capabilities

Each provider client must declare a set of capabilities.

Recommended v1 capabilities:

- `text_generation`
- `json_schema_output`
- `token_usage`
- `cached_input_usage`
- `reasoning_token_usage`
- `thinking_time`
- `subprocess`

Requests may mark capabilities as required.

If a required capability is missing, the caller must raise an unsupported-capability error before making the request.

Translation requires:

- `text_generation`
- `json_schema_output`

Translation should request usage fields, but it must tolerate missing optional accounting fields by recording `null`.

## Authentication

Provider clients support these auth modes in v1:

- `api_key`
  Used by `openai_api` and optionally by `codex_cli`.
- `chatgpt`
  Used by `codex_cli` when the local Codex installation is logged in with ChatGPT-managed Codex access.
- `cached`
  Reuse whatever auth the provider already has cached locally.

Provider auth resolution must be explicit in configuration or CLI flags.

Auth config is owned by `curio.llm_caller` in v1. A separate Curio auth module should not be introduced unless another subsystem needs the same auth model.

Authentication mode is provider configuration, not a workflow-requested capability. Curio workflows must not list auth modes in `required_capabilities`.

The LLM caller must not:

- read `~/.codex/auth.json` directly
- print credentials
- store API keys in Curio payloads
- copy provider auth files

`codex_cli` may rely on the installed Codex CLI's own cached authentication.

## Request Shape

The stable JSON representation of an LLM request is:

```json
{
  "llm_request_version": "curio-llm-request.v1",
  "request_id": "translate-20260424-000001",
  "workflow": "translate",
  "instructions": "Return only JSON that satisfies the provided schema.",
  "input": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Use the translation request JSON below to classify language and conditionally translate each block into English."
        }
      ]
    }
  ],
  "output": {
    "type": "json_schema",
    "name": "curio_translation_model_output",
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "properties": {}
    },
    "strict": true
  },
  "required_capabilities": [
    "text_generation",
    "json_schema_output"
  ],
  "metadata": {
    "source": "curio.translate",
    "llm_caller": "translator_codex_gpt_54_mini"
  }
}
```

Fields:

- `llm_request_version`
  Fixed v1 request contract identifier. In v1 this must be `curio-llm-request.v1`.
- `request_id`
  Operator-visible identifier for logs and diagnostics.
- `workflow`
  Curio workflow name, such as `translate` or `curate`.
- `instructions`
  System-level instruction text owned by the workflow.
- `input`
  Ordered message list. V1 content parts are text-only. Workflows may serialize richer structured context, such as translation blocks and thresholds, inside those text parts.
- `output`
  Requested output format. V1 requires `json_schema` for machine-read workflows. The schema should describe the model-emitted payload, not provider usage metadata that Curio adds after the call.
- `required_capabilities`
  Capabilities that must be supported before calling the provider.
- `metadata`
  Small diagnostic object. It must not contain secrets or large source text duplicated from `input`.

## Response Shape

The stable JSON representation of an LLM response is:

```json
{
  "llm_response_version": "curio-llm-response.v1",
  "request_id": "translate-20260424-000001",
  "status": "succeeded",
  "provider": "codex_cli",
  "model": "gpt-5.3-codex",
  "output": {
    "type": "json",
    "value": {
      "request_id": "translate-20260424-000001",
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
      ]
    }
  },
  "usage": {
    "input_tokens": 24763,
    "cached_input_tokens": 24448,
    "output_tokens": 122,
    "reasoning_tokens": null,
    "total_tokens": 24885,
    "metered_objects": [],
    "started_at": "2026-04-24T15:20:00Z",
    "completed_at": "2026-04-24T15:20:07Z",
    "wall_seconds": 7.0,
    "thinking_seconds": null
  },
  "warnings": []
}
```

Fields:

- `llm_response_version`
  Fixed v1 response contract identifier. In v1 this must be `curio-llm-response.v1`.
- `request_id`
  The request identifier from the input.
- `status`
  One of `succeeded`, `failed`, or `cancelled`.
- `provider`
  Provider identifier actually used.
- `model`
  Provider model actually used, if known.
- `output`
  The parsed provider result. Machine-read workflows should use `type = json`. This may be `null` only when a non-success response is returned instead of a typed exception.
- `usage`
  Token, metered-object, and timing data.
- `warnings`
  Compact operational warnings.

## Usage And Timing

`LlmUsage` must expose:

- `input_tokens`
- `cached_input_tokens`
- `output_tokens`
- `reasoning_tokens`
- `total_tokens`
- `metered_objects`
- `started_at`
- `completed_at`
- `wall_seconds`
- `thinking_seconds`

`metered_objects` is an ordered list for non-token usage units such as images, audio minutes, or provider-specific billed units. Each item should include:

- `name`
- `quantity`
- `unit`

Exact model "thinking time" is not a portable provider primitive. The caller must record `thinking_seconds` only when the provider explicitly exposes it. Otherwise it must be `null`. The caller should always record wall-clock timing around the provider invocation.

Codex CLI usage should be captured from `codex exec --json` JSONL events. `CodexCliClient` should read the `turn.completed.usage` object and map documented fields such as `input_tokens`, `cached_input_tokens`, and `output_tokens` into `LlmUsage`. It should compute `total_tokens` when the provider does not emit it directly. It should measure `started_at`, `completed_at`, and `wall_seconds` locally around the subprocess invocation.

## Provider Client Responsibilities

Each provider client is responsible for:

- mapping `LlmRequest` to the provider API or CLI
- applying provider-specific auth without exposing secrets to Curio workflows
- enforcing timeout behavior
- requesting strict schema output when available
- parsing provider output into `LlmResponse`
- collecting usage and timing fields
- returning compact warnings
- raising typed errors for auth failures, unsupported capabilities, invalid provider output, timeouts, and non-zero subprocess exits

Provider clients should be small and boring. Most workflow logic belongs above the provider boundary.

## `openai_api` Client

`OpenAiApiClient` is a first-class v1 provider client. It is selected only through an explicit named caller config.

It should:

- authenticate with an API key
- call the Responses API
- request JSON Schema output for structured workflows
- capture provider usage fields that are present
- surface API errors as typed Curio errors

It should not depend on Codex CLI state.

API usage is separate from ChatGPT subscription usage and is billed through the API account.

## `codex_cli` Client

`CodexCliClient` is the default v1 provider client for normal Curio workflows.

It should:

- shell out to `codex exec`
- pass task text through stdin or a temporary prompt file
- pass the workflow JSON Schema via `--output-schema`
- prefer `--ephemeral`
- run with read-only sandbox settings for translation
- parse JSONL events when `--json` is enabled
- extract the final agent message and `turn.completed.usage` event
- measure wall-clock time locally around the subprocess
- fail if the final message is not valid JSON matching the requested schema

`codex_cli` is an agent subprocess, not a low-level completion API. It may have more overhead and more operational variance than direct API calls. Curio should therefore treat it as a supported provider, not as the only implementation path.

When Codex CLI is authenticated through ChatGPT-managed Codex access, usage consumes Codex plan limits or credits. When it is authenticated with an API key, usage follows API billing for that key.

## Provider Clients

The selected provider client owns all provider-specific request and response mapping.

The recommended shape is:

- Curio chooses one provider during CLI or configuration setup.
- Curio constructs the matching `LlmClient`.
- Workflow services receive that `LlmClient` as a dependency.
- The provider client transforms `LlmRequest` into provider-specific API or CLI calls.
- The provider client transforms provider output back into `LlmResponse`.
- Workflow validates and consumes only the provider-neutral response.

V1 does not include provider routing or provider fallback.

## Retry Policy

Retries are owned by `curio.llm_caller`.

V1 should support bounded retry configuration for:

- invalid JSON output
- schema-invalid JSON output
- transient provider or subprocess failures

Translation should not implement its own retry loop. It should receive either a valid `LlmResponse` or a typed LLM-caller error after retries are exhausted.

## Failure Semantics

The LLM caller should distinguish:

- configuration errors
- missing provider executable
- auth errors
- unsupported capability errors
- provider timeout errors
- provider rejected request errors
- invalid output errors
- schema validation errors

Machine-callable workflows should receive typed exceptions. CLI commands should translate those exceptions into compact stderr messages and non-zero exit codes.

## Acceptance Scenarios

The LLM caller spec is satisfied only if all of the following are true:

- a translation workflow can call an injected `LlmClient` without importing provider-specific modules
- `openai_api` and `codex_cli` can both satisfy the same structured-output request shape
- missing required capabilities fail before network or subprocess work begins
- token usage is captured when the provider returns it
- Codex CLI wall time is measured locally
- unavailable token or thinking-time fields are represented as `null`, not guessed
- provider raw responses are not required by downstream Curio modules
- no secret values are printed, persisted in payloads, or exposed in exceptions
