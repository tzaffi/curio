# Curio Authentication

This guide explains where Curio secrets live and how to set them up.

Think of Curio like a helper that needs a locked box. The secret goes in the
locked box. Curio remembers only the label on the box.

For macOS, the locked box is Keychain. In Python, Curio reads Keychain through
the `keyring` package.

## Links

- OpenAI API key dashboard: <https://platform.openai.com/api-keys>
- OpenAI API authentication docs: <https://developers.openai.com/api/reference/overview#authentication>
- Codex authentication docs: <https://developers.openai.com/codex/auth>
- Codex CLI and Sign in with ChatGPT help: <https://help.openai.com/en/articles/11381614>

## What Goes Where

Curio has two OpenAI-related provider paths:

- `openai_api`
  Curio calls the OpenAI API directly. Curio needs an OpenAI API key, and that
  key must live in Keychain.
- `codex_cli`
  Curio asks the `codex` command to do the provider work. Codex owns its own
  login. Curio should not copy Codex OAuth tokens.

Auth is provider configuration. It is not an LLM capability and must not appear
in `LlmRequest.required_capabilities`.

## OpenAI API Key Setup

Use this when Curio will call the OpenAI API directly.

1. Open the API key dashboard:
   <https://platform.openai.com/api-keys>

2. Sign in to the OpenAI account you want Curio to bill against.

3. Create a new API key.

4. Copy the key when the dashboard shows it.

5. Store the key in Keychain using Python `keyring`:

   ```bash
   uv run python -m keyring set curio/openai-api default-api-key
   ```

6. Paste the API key when prompted.

7. Press Return.

`config.example.openai_api.json` uses this locator:

```text
service = curio/openai-api
account = default-api-key
```

Curio stores that locator in `config.json`. Curio does not store the API key in
repo files, JSON payloads, logs, CLI args, shell profiles, or environment
variables.

## Codex CLI With ChatGPT Login

Use this when Curio will call the `codex` command and you want Codex to use
your ChatGPT subscription login.

1. Install Codex if needed:

   ```bash
   npm i -g @openai/codex
   ```

2. Tell Codex to store cached credentials in the OS keyring.

   Open `~/.codex/config.toml` and add `cli_auth_credentials_store` at the
   top level of the file. Do not put it under any `[projects."..."]` section.
   Existing project sections can stay below it.

   ```toml
   # ~/.codex/config.toml
   cli_auth_credentials_store = "keyring"

   [projects."/Users/zeph/github/tzaffi/curio"]
   trust_level = "trusted"
   ```

3. Log in:

   ```bash
   codex login
   ```

4. Complete the browser login.

If browser login is awkward or the machine is headless, use device auth:

```bash
codex login --device-auth
```

Codex docs say the CLI caches login details locally and can use the OS
credential store. For ChatGPT sessions, Codex refreshes tokens during active
use before they expire. That means you usually should not have to log in every
new shell session.

You may need to log in again if:

- you run `codex logout`
- the token is revoked
- the cached login is deleted
- OpenAI/Codex decides the session is invalid
- your workspace/login policy changes
- the configured credential store changes

## Codex CLI With API Key Login

> ⚠️ **WARNING: API-key login changes the billing/auth path.**
>
> Use this advanced fallback only when you intentionally want Codex CLI usage
> billed through an OpenAI API key instead of ChatGPT subscription access.
> Prefer ChatGPT login for normal Curio use. Never paste API keys into shell
> history, config files, logs, or chat.

Curio's default API-key locator for Codex is:

```text
service = curio/codex-cli
account = default-api-key
```

If Codex API-key mode is later enabled for Curio-owned handoff, put only this
locator metadata in `config.json`, never the raw key.

Store the key:

```bash
uv run python -m keyring set curio/codex-cli default-api-key
```

Then let Codex read it through stdin:

```bash
uv run python -m keyring get curio/codex-cli default-api-key | codex login --with-api-key
```

Do not run `keyring get` by itself in a terminal unless you are prepared for it
to print the secret. Do not paste the key into shell history, config files,
logs, or chat.

## What Curio Must Not Do

Curio must not:

- store API keys in repo files
- store API keys in JSON request or response payloads
- accept raw API keys as CLI flags
- require `OPENAI_API_KEY` as the normal runtime path
- print secrets to stdout or stderr
- include secrets in exception messages
- copy Codex OAuth, access, or refresh tokens into Curio-owned storage

## Testing Rules

`make check` must not require:

- a real OpenAI API key
- network access
- `codex login`
- a real Codex binary
- a real Keychain item

Tests use in-memory secret stores and fake provider fixtures. Live provider
smoke tests must be opt-in only.
