# Curio Usage

Curio reads explicit runtime configuration from `config.json`. It does not fall
back to checked-in example files.

## Pick A Provider Config

Use Codex CLI through your ChatGPT login:

```bash
cp config.example.codex_cli.json config.json
```

Use the OpenAI API directly:

```bash
cp config.example.openai_api.json config.json
```

Then edit `config.json`. The file may contain one provider or both providers,
but the provider you pass to `curio translate --provider ...` must exist in
`config.json`.

Raw secrets do not go in `config.json`. Only Keychain locator metadata belongs
there.

## Codex CLI Values

Use `config.example.codex_cli.json` for `--provider codex_cli`.

Important fields:

- `providers.codex_cli.auth.mode`: use `chatgpt` for normal ChatGPT-plan login.
- `providers.codex_cli.auth.require_keyring_credentials_store`: keep this `true`.
- `providers.codex_cli.exec.executable`: usually `codex`.
- `providers.codex_cli.exec.sandbox`: usually `read-only`.

Before running Curio with Codex CLI, configure Codex auth as described in
[AUTHENTICATION.md](AUTHENTICATION.md), including the top-level
`cli_auth_credentials_store = "keyring"` setting in `~/.codex/config.toml`.

Run a translation:

```bash
uv run curio translate --provider codex_cli --model YOUR_MODEL "bonjour"
```

## OpenAI API Values

Use `config.example.openai_api.json` for `--provider openai_api`.

Important fields:

- `providers.openai_api.auth.api_key_ref.service`
- `providers.openai_api.auth.api_key_ref.account`
- `providers.openai_api.auth.organization`
- `providers.openai_api.auth.project`

Store the API key in Keychain at the configured locator:

```bash
uv run python -m keyring set curio/openai-api default-api-key
```

The API key dashboard is here:

<https://platform.openai.com/api-keys>

`organization` and `project` may be `null` when the key itself is already
scoped the way you want. If you need explicit headers, OpenAI documents that
organization IDs are found on the organization settings page and project IDs
are found on the selected project's general settings page:

<https://platform.openai.com/docs/api-reference>

The Projects API reference shows project IDs in the `proj_...` form:

<https://platform.openai.com/docs/api-reference/projects>

Run a translation:

```bash
uv run curio translate --provider openai_api --model YOUR_MODEL "bonjour"
```

## Custom Config Path

Use `--config` when the file is not `./config.json`:

```bash
uv run curio translate --config ./my-curio-config.json --provider openai_api --model YOUR_MODEL "bonjour"
```

## Expected Fail-Fast Behavior

Curio fails instead of guessing when:

- `config.json` is missing
- the selected provider is not present in config
- provider auth config is missing
- Codex CLI exec config is missing
- `--provider` is missing for raw text input
- OpenAI API or Codex CLI model is missing

See [AUTHENTICATION.md](AUTHENTICATION.md) for the secure setup details.
