import json
from pathlib import Path

import pytest

from curio import config as config_module
from curio.config import ConfigError, load_config
from curio.llm_caller import (
    CodexCliAuthConfig,
    CodexCliAuthMode,
    OpenAiApiAuthConfig,
    ProviderName,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def write_config(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_config_path_points_to_current_working_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    assert config_module.config_path() == tmp_path / "config.json"


def test_checked_in_codex_example_config_parses() -> None:
    config = load_config(repo_root() / "config.example.codex_cli.json")
    provider_config = config.provider_config(ProviderName.CODEX_CLI)

    assert isinstance(provider_config.auth_config, CodexCliAuthConfig)
    assert provider_config.auth_config.mode == CodexCliAuthMode.CHATGPT
    assert provider_config.auth_config.require_keyring_credentials_store is True
    assert provider_config.codex_exec_config is not None
    assert provider_config.codex_exec_config.executable == "codex"
    assert provider_config.codex_exec_config.sandbox == "read-only"
    assert provider_config.codex_exec_config.color == "never"
    assert provider_config.codex_exec_config.ephemeral is True
    assert provider_config.codex_exec_config.json_events is True


def test_checked_in_openai_example_config_parses() -> None:
    config = load_config(repo_root() / "config.example.openai_api.json")
    provider_config = config.provider_config("openai_api")

    assert isinstance(provider_config.auth_config, OpenAiApiAuthConfig)
    assert provider_config.auth_config.api_key_ref.service == "curio/openai-api"
    assert provider_config.auth_config.api_key_ref.account == "default-api-key"
    assert provider_config.auth_config.organization is None
    assert provider_config.auth_config.project is None
    assert provider_config.codex_exec_config is None


def test_load_config_requires_file_and_json_object(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing-config.json"
    monkeypatch.setattr(config_module, "config_path", lambda: missing)

    with pytest.raises(ConfigError, match="Missing config file"):
        load_config()

    invalid = tmp_path / "invalid.json"
    invalid.write_text("[", encoding="utf-8")
    with pytest.raises(ConfigError, match="valid JSON"):
        load_config(invalid)

    not_object = tmp_path / "not-object.json"
    not_object.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError, match="JSON object"):
        load_config(not_object)


def test_load_config_requires_providers_and_selected_provider(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path, {"providers": {}})

    with pytest.raises(ConfigError, match="at least one provider"):
        load_config(config_path)

    config = load_config(repo_root() / "config.example.openai_api.json")
    with pytest.raises(ConfigError, match="providers.codex_cli"):
        config.provider_config("codex_cli")


def test_load_config_rejects_invalid_provider_blocks(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path, {"providers": "not-an-object"})
    with pytest.raises(ConfigError, match="providers"):
        load_config(config_path)

    write_config(config_path, {"providers": {"bogus": {}}})
    with pytest.raises(ValueError, match="bogus"):
        load_config(config_path)

    write_config(config_path, {"providers": {"openai_api": {"auth": "bad"}}})
    with pytest.raises(ConfigError, match="providers.openai_api.auth"):
        load_config(config_path)

    write_config(
        config_path,
        {
            "providers": {
                "codex_cli": {
                    "auth": {
                        "provider": "codex_cli",
                        "mode": "chatgpt",
                        "api_key_ref": None,
                        "require_keyring_credentials_store": True,
                    }
                }
            }
        },
    )
    with pytest.raises(ConfigError, match="providers.codex_cli.exec"):
        load_config(config_path)


def test_load_config_rejects_invalid_codex_exec_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    payload["providers"]["codex_cli"]["exec"]["extra_config"] = "bad"
    write_config(config_path, payload)

    with pytest.raises(ConfigError, match="extra_config"):
        load_config(config_path)

    payload["providers"]["codex_cli"]["exec"]["extra_config"] = [""]
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="extra_config item"):
        load_config(config_path)

    payload["providers"]["codex_cli"]["exec"]["extra_config"] = []
    payload["providers"]["codex_cli"]["exec"]["ephemeral"] = "true"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="ephemeral"):
        load_config(config_path)
