from typing import cast

import pytest
from keyring.errors import KeyringError, KeyringLocked

import curio.llm_caller.auth as auth
from curio.llm_caller import (
    CodexCliAuthConfig,
    CodexCliAuthMode,
    InMemorySecretStore,
    KeyringSecretStore,
    OpenAiApiAuthConfig,
    ProviderAuthConfigError,
    SecretBackend,
    SecretLookupError,
    SecretRef,
    resolve_codex_api_key,
    resolve_openai_api_key,
    secret_ref_cache_key,
)


def make_secret_ref() -> SecretRef:
    return SecretRef(service="curio/openai-api", account="default-api-key", label="OpenAI API key")


def test_secret_ref_serializes_locator_without_secret_value() -> None:
    secret_ref = make_secret_ref()
    payload = secret_ref.to_json()

    assert secret_ref.backend == SecretBackend.KEYRING
    assert payload == {
        "backend": "keyring",
        "service": "curio/openai-api",
        "account": "default-api-key",
        "label": "OpenAI API key",
    }
    assert SecretRef.from_json(payload) == secret_ref
    assert secret_ref_cache_key(secret_ref) == ("keyring", "curio/openai-api", "default-api-key")


def test_secret_ref_rejects_invalid_locator_shapes() -> None:
    with pytest.raises(ValueError, match="secret service must be a string"):
        SecretRef(service=cast(str, None), account="default-api-key")

    with pytest.raises(ValueError, match="secret service must not be empty"):
        SecretRef(service=" ", account="default-api-key")

    with pytest.raises(ValueError, match="secret label must not be empty"):
        SecretRef(service="curio/openai-api", account="default-api-key", label="")

    with pytest.raises(ValueError, match="secret ref must be an object"):
        SecretRef.from_json([])

    with pytest.raises(ValueError, match="account is required"):
        SecretRef.from_json({"backend": "keyring", "service": "curio/openai-api"})


def test_in_memory_secret_store_resolves_and_invalidates_without_leaking_secret() -> None:
    secret_ref = make_secret_ref()
    secret = "sk-test-secret"
    store = InMemorySecretStore()

    store.set_secret(secret_ref, secret)

    assert store.get_secret(secret_ref) == secret
    assert secret not in repr(store)

    store.invalidate(secret_ref)
    with pytest.raises(SecretLookupError) as missing:
        store.get_secret(secret_ref)
    assert str(missing.value) == auth.MISSING_CREDENTIAL_DETAIL
    assert secret not in str(missing.value)

    store.set_secret(secret_ref, secret)
    store.invalidate()
    with pytest.raises(SecretLookupError, match=auth.MISSING_CREDENTIAL_DETAIL):
        store.get_secret(secret_ref)

    with pytest.raises(ValueError, match="secret must not be empty"):
        store.set_secret(secret_ref, "")


def test_keyring_secret_store_reads_and_reports_generic_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    secret_ref = make_secret_ref()
    secret = "sk-test-secret"
    store = KeyringSecretStore()

    monkeypatch.setattr(auth.keyring, "get_password", lambda service, account: secret)

    assert store.get_secret(secret_ref) == secret

    monkeypatch.setattr(auth.keyring, "get_password", lambda service, account: None)
    with pytest.raises(SecretLookupError) as missing:
        store.get_secret(secret_ref)
    assert str(missing.value) == auth.MISSING_CREDENTIAL_DETAIL

    def raise_keyring_error(service: str, account: str) -> str:
        raise KeyringLocked(f"locked while reading {secret}")

    monkeypatch.setattr(auth.keyring, "get_password", raise_keyring_error)
    with pytest.raises(SecretLookupError) as failed:
        store.get_secret(secret_ref)
    assert str(failed.value) == auth.SECURE_STORE_ACCESS_FAILED_DETAIL
    assert secret not in str(failed.value)
    assert failed.value.error_code == "secure_store_access_failed"

    store.invalidate(secret_ref)


def test_openai_auth_config_round_trips_and_resolves_key_without_payload_leak(capsys: pytest.CaptureFixture[str]) -> None:
    secret_ref = make_secret_ref()
    config = OpenAiApiAuthConfig(
        api_key_ref=secret_ref,
        organization="org_test",
        project="proj_test",
    )
    secret = "sk-test-secret"
    store = InMemorySecretStore()
    store.set_secret(secret_ref, secret)

    payload = config.to_json()

    assert payload["provider"] == "openai_api"
    assert payload["api_key_ref"] == secret_ref.to_json()
    assert OpenAiApiAuthConfig.from_json(payload) == config
    assert resolve_openai_api_key(config, store) == secret

    print(payload)
    captured = capsys.readouterr()
    assert secret not in repr(config)
    assert secret not in str(payload)
    assert secret not in captured.out
    assert secret not in captured.err


def test_openai_auth_config_rejects_wrong_provider_and_empty_fields() -> None:
    payload = OpenAiApiAuthConfig().to_json()
    payload["provider"] = "codex_cli"

    with pytest.raises(ProviderAuthConfigError, match="provider must be openai_api"):
        OpenAiApiAuthConfig.from_json(payload)

    with pytest.raises(ValueError, match="organization must not be empty"):
        OpenAiApiAuthConfig(organization="")

    with pytest.raises(ValueError, match="project must not be empty"):
        OpenAiApiAuthConfig(project=" ")


def test_codex_chatgpt_auth_config_round_trips_without_curio_secret() -> None:
    config = CodexCliAuthConfig()
    payload = config.to_json()

    assert config.mode == CodexCliAuthMode.CHATGPT
    assert payload == {
        "provider": "codex_cli",
        "mode": "chatgpt",
        "api_key_ref": None,
        "require_keyring_credentials_store": True,
    }
    assert CodexCliAuthConfig.from_json(payload) == config


def test_codex_api_key_auth_config_defaults_and_resolves_key() -> None:
    config = CodexCliAuthConfig(mode=CodexCliAuthMode.API_KEY, require_keyring_credentials_store=False)
    secret = "sk-codex-secret"
    store = InMemorySecretStore()
    assert config.api_key_ref is not None
    store.set_secret(config.api_key_ref, secret)

    assert config.mode == CodexCliAuthMode.API_KEY
    assert config.api_key_ref.service == auth.DEFAULT_CODEX_API_KEY_SERVICE
    assert resolve_codex_api_key(config, store) == secret
    assert CodexCliAuthConfig.from_json(config.to_json()) == config
    assert secret not in str(config.to_json())


def test_codex_auth_config_rejects_invalid_combinations() -> None:
    secret_ref = make_secret_ref()

    with pytest.raises(ProviderAuthConfigError, match="chatgpt auth must not include"):
        CodexCliAuthConfig(mode=CodexCliAuthMode.CHATGPT, api_key_ref=secret_ref)

    with pytest.raises(ValueError, match="require_keyring_credentials_store must be a boolean"):
        CodexCliAuthConfig(require_keyring_credentials_store=cast(bool, "true"))

    payload = CodexCliAuthConfig().to_json()
    payload["provider"] = "openai_api"
    with pytest.raises(ProviderAuthConfigError, match="provider must be codex_cli"):
        CodexCliAuthConfig.from_json(payload)

    with pytest.raises(ValueError, match="require_keyring_credentials_store is required"):
        CodexCliAuthConfig.from_json({"provider": "codex_cli", "mode": "chatgpt"})

    with pytest.raises(ProviderAuthConfigError, match="does not use a Curio API key"):
        resolve_codex_api_key(CodexCliAuthConfig(), InMemorySecretStore())


def test_keyring_backend_exception_text_is_not_exposed(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "sk-test-secret"

    def raise_keyring_error(service: str, account: str) -> str:
        raise KeyringError(f"backend included {secret}")

    monkeypatch.setattr(auth.keyring, "get_password", raise_keyring_error)

    with pytest.raises(SecretLookupError) as exc:
        KeyringSecretStore().get_secret(make_secret_ref())

    assert str(exc.value) == auth.SECURE_STORE_ACCESS_FAILED_DETAIL
    assert secret not in str(exc.value)
