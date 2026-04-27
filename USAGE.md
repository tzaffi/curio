# Curio Usage

Curio reads explicit runtime configuration from `config.json`. It does not fall
back to checked-in example files.

## Pick LLM Callers

Use Codex CLI through your ChatGPT login:

```bash
cp config.example.codex_cli.json config.json
```

Use the OpenAI API directly:

```bash
cp config.example.openai_api.json config.json
```

Then edit `config.json`. The file contains named `llm_callers` and a
`translate.llm_caller` default. Normal translation commands use that configured
default. Pass `--llm-caller NAME` only when you want to override the config or
structured JSON request for one run.

Each named caller owns its provider, model, auth config, timeout, and
provider-specific tuning. Translator callers in the example configs also define
`prompt` templates for model-specific translator instructions and user prompt
text. Runtime model overrides are intentionally not supported.

Raw secrets do not go in `config.json`. Only Keychain locator metadata belongs
there.

## Codex CLI Values

Use a Codex caller such as `translator_codex_gpt_55` or `translator_codex_gpt_54_mini`.

Important fields:

- `llm_callers.NAME.provider`: `codex_cli`
- `llm_callers.NAME.model`: the Codex model for this named caller
- `llm_callers.NAME.timeout_seconds`: provider-call wall-clock timeout
- `llm_callers.NAME.prompt.instructions`: optional translator instructions template
- `llm_callers.NAME.prompt.user`: optional translator user prompt template
- `llm_callers.NAME.pricing`: optional API-equivalent pricing for cost estimates
- `llm_callers.NAME.auth.mode`: use `chatgpt` for normal ChatGPT-plan login
- `llm_callers.NAME.exec.model_reasoning_effort`: optional Codex reasoning effort
- `llm_callers.NAME.exec.model_verbosity`: optional Codex verbosity

Before running Curio with Codex CLI, configure Codex auth as described in
[AUTHENTICATION.md](AUTHENTICATION.md), including the top-level
`cli_auth_credentials_store = "keyring"` setting in `~/.codex/config.toml`.

Run a translation:

```bash
uv run curio translate "bonjour"
```

## OpenAI API Values

Use an OpenAI caller such as `translator_openai_gpt_54_mini_cold`.

Important fields:

- `llm_callers.NAME.provider`: `openai_api`
- `llm_callers.NAME.model`: the OpenAI model for this named caller
- `llm_callers.NAME.timeout_seconds`: provider-call wall-clock timeout
- `llm_callers.NAME.prompt.instructions`: optional translator instructions template
- `llm_callers.NAME.prompt.user`: optional translator user prompt template
- `llm_callers.NAME.pricing`: optional API-equivalent pricing for cost estimates
- `llm_callers.NAME.auth.api_key_ref.service`
- `llm_callers.NAME.auth.api_key_ref.account`
- `llm_callers.NAME.responses.temperature`
- `llm_callers.NAME.responses.reasoning_effort`
- `llm_callers.NAME.responses.max_output_tokens`
- `llm_callers.NAME.responses.text_verbosity`

Store the API key in Keychain at the configured locator:

```bash
uv run python -m keyring set curio/openai-api default-api-key
```

The API key dashboard is here:

<https://platform.openai.com/api-keys>

`organization` and `project` may be `null` when the key itself is already
scoped the way you want.

Run a translation:

```bash
uv run curio translate "bonjour"
```

## Pricing Values

Pricing is optional. Curio uses it only to compute local cost estimates from
provider token usage. The estimate is not a billing statement. This distinction
matters especially for `codex_cli` callers that use ChatGPT auth: Curio can show
an API-equivalent estimate, but the run is not literally billed through the API.

Use the official OpenAI API pricing page as the source for these fields:
<https://openai.com/api/pricing/>

Model-specific API docs can be cross-checked here:
<https://developers.openai.com/api/docs/models>

Configured pricing lives under each named caller:

```json
{
  "llm_callers": {
    "translator_codex_gpt_55": {
      "pricing": {
        "currency": "USD",
        "basis": "api_equivalent",
        "input_price_per_million": 5.0,
        "cached_input_price_per_million": 0.5,
        "output_price_per_million": 30.0
      }
    }
  }
}
```

If pricing is omitted, translation JSON still includes `llm.usage`, but
`llm.cost_estimate` is `null` and `--stats` reports cost as unavailable.

## Custom Config Path

Use `--config` when the file is not `./config.json`:

```bash
uv run curio translate --config ./my-curio-config.json "bonjour"
```

Override the configured translation caller for one run:

```bash
uv run curio translate --llm-caller translator_openai_gpt_54_mini_cold "bonjour"
```

Translation caller precedence is:

1. CLI `--llm-caller`
2. structured JSON `llm_caller`
3. `config.json` `translate.llm_caller`

## Prompt Overrides

Use `prompt` only for translator-specific named callers, usually with a
`translator_` prefix. The example configs include the default translator prompt;
customize it per named caller when a model needs different wording:

```json
{
  "llm_callers": {
    "translator_codex_gpt_54_mini": {
      "prompt": {
        "instructions": "Return only JSON for translation request {request_id}.",
        "user": "Translate with threshold {english_confidence_threshold}.\n\nRequest:\n{translation_request_json}\n\nSchema:\n{output_schema_json}"
      }
    }
  }
}
```

Supported placeholders are `{translation_request_json}`, `{output_schema_json}`,
`{request_id}`, `{target_language}`, and `{english_confidence_threshold}`.
Literal braces use normal Python escaping: `{{` and `}}`.

## Expected Fail-Fast Behavior

Curio fails instead of guessing when:

- `config.json` is missing
- the selected named LLM caller is not present in config
- provider auth config is missing
- provider-specific runtime config is missing
- no LLM caller is available from `--llm-caller`, structured JSON, or `translate.llm_caller`
- a named caller has an invalid model, timeout, or tuning value

See [AUTHENTICATION.md](AUTHENTICATION.md) for the secure setup details.

## Live Translation Smoke Tests

Live smoke tests are opt-in and Codex CLI-only. They are not part of
`make check`.

Use:

```bash
make translate-smoke
make translate-smoke-evaluate
```

See [SMOKE-TESTS.md](SMOKE-TESTS.md) for prerequisites, the reviewed case/model
matrix, artifact locations, evaluator workflow, and common failure messages.
See [the current smoke-test upshot](reports/translate-smoke/20260426-060103-22de460b22c0/UPSHOT.md) for the recommended translation caller.
