import json
from pathlib import Path

import pytest

from curio import config as config_module
from curio.config import ConfigError, CurioConfig, TranslateConfig, load_config
from curio.llm_caller import (
    CodexCliAuthConfig,
    CodexCliAuthMode,
    CodexCliReasoningEffort,
    CodexCliVerbosity,
    OpenAiApiAuthConfig,
    OpenAiReasoningEffort,
    OpenAiTextVerbosity,
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
    caller_config = config.llm_caller_config("codex_gpt_55")

    assert config.translate_config == TranslateConfig(llm_caller="codex_gpt_54_mini")
    assert caller_config.provider == ProviderName.CODEX_CLI
    assert caller_config.model == "gpt-5.5"
    assert caller_config.timeout_seconds == 300
    assert isinstance(caller_config.auth_config, CodexCliAuthConfig)
    assert caller_config.auth_config.mode == CodexCliAuthMode.CHATGPT
    assert caller_config.auth_config.require_keyring_credentials_store is True
    assert caller_config.codex_exec_config is not None
    assert caller_config.codex_exec_config.executable == "codex"
    assert caller_config.codex_exec_config.sandbox == "read-only"
    assert caller_config.codex_exec_config.color == "never"
    assert caller_config.codex_exec_config.ephemeral is True
    assert caller_config.codex_exec_config.json_events is True
    assert caller_config.codex_exec_config.model_reasoning_effort == CodexCliReasoningEffort.LOW
    assert caller_config.codex_exec_config.model_verbosity is None

    mini_config = config.llm_caller_config("codex_gpt_54_mini")
    assert mini_config.model == "gpt-5.4-mini"
    assert mini_config.codex_exec_config is not None
    assert mini_config.codex_exec_config.model_verbosity == CodexCliVerbosity.LOW


def test_checked_in_openai_example_config_parses() -> None:
    config = load_config(repo_root() / "config.example.openai_api.json")
    caller_config = config.llm_caller_config("openai_gpt_54_mini_cold")

    assert config.translate_config == TranslateConfig(llm_caller="openai_gpt_54_mini_cold")
    assert caller_config.provider == ProviderName.OPENAI_API
    assert caller_config.model == "gpt-5.4-mini"
    assert caller_config.timeout_seconds == 300
    assert isinstance(caller_config.auth_config, OpenAiApiAuthConfig)
    assert caller_config.auth_config.api_key_ref.service == "curio/openai-api"
    assert caller_config.auth_config.api_key_ref.account == "default-api-key"
    assert caller_config.auth_config.organization is None
    assert caller_config.auth_config.project is None
    assert caller_config.codex_exec_config is None
    assert caller_config.openai_responses_config is not None
    assert caller_config.openai_responses_config.temperature == 0
    assert caller_config.openai_responses_config.reasoning_effort == OpenAiReasoningEffort.LOW
    assert caller_config.openai_responses_config.max_output_tokens is None
    assert caller_config.openai_responses_config.text_verbosity == OpenAiTextVerbosity.LOW


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


def test_load_config_requires_llm_callers_and_selected_caller(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path, {"llm_callers": {}})

    with pytest.raises(ConfigError, match="at least one llm_caller"):
        load_config(config_path)

    config = load_config(repo_root() / "config.example.openai_api.json")
    with pytest.raises(ConfigError, match="llm_callers.codex_gpt_55"):
        config.llm_caller_config("codex_gpt_55")


def test_load_config_parses_optional_translate_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    del payload["translate"]
    write_config(config_path, payload)

    config = load_config(config_path)

    assert config.translate_config == TranslateConfig()


def test_load_config_rejects_invalid_translate_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))

    payload["translate"] = "bad"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="translate"):
        load_config(config_path)

    payload["translate"] = {"llm_caller": ""}
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="translate.llm_caller"):
        load_config(config_path)

    payload["translate"] = {"llm_caller": "missing_caller"}
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="llm_callers.missing_caller"):
        load_config(config_path)

    with pytest.raises(ConfigError, match="TranslateConfig"):
        CurioConfig(llm_callers={}, translate_config="bad")


def test_load_config_rejects_invalid_llm_caller_blocks(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    write_config(config_path, {"llm_callers": "not-an-object"})
    with pytest.raises(ConfigError, match="llm_callers"):
        load_config(config_path)

    write_config(config_path, {"llm_callers": {"bogus": {"provider": "bogus"}}})
    with pytest.raises(ValueError, match="bogus"):
        load_config(config_path)

    write_config(config_path, {"llm_callers": {"bad_openai": {"provider": "openai_api", "auth": "bad"}}})
    with pytest.raises(ConfigError, match="llm_callers.bad_openai.auth"):
        load_config(config_path)

    write_config(
        config_path,
        {
            "llm_callers": {
                "codex_gpt_55": {
                    "provider": "codex_cli",
                    "model": "gpt-5.5",
                    "timeout_seconds": 300,
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
    with pytest.raises(ConfigError, match="llm_callers.codex_gpt_55.exec"):
        load_config(config_path)


def test_load_config_rejects_invalid_codex_exec_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["codex_gpt_55"]["exec"]["extra_config"] = "bad"
    write_config(config_path, payload)

    with pytest.raises(ConfigError, match="extra_config"):
        load_config(config_path)

    payload["llm_callers"]["codex_gpt_55"]["exec"]["extra_config"] = [""]
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="extra_config item"):
        load_config(config_path)

    payload["llm_callers"]["codex_gpt_55"]["exec"]["extra_config"] = []
    payload["llm_callers"]["codex_gpt_55"]["exec"]["ephemeral"] = "true"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="ephemeral"):
        load_config(config_path)


def test_load_config_rejects_invalid_named_caller_runtime_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.openai_api.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["openai_gpt_54_mini_cold"]["timeout_seconds"] = 0
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="timeout_seconds"):
        load_config(config_path)

    payload = json.loads((repo_root() / "config.example.openai_api.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["openai_gpt_54_mini_cold"]["responses"]["temperature"] = "cold"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="temperature"):
        load_config(config_path)

    payload["llm_callers"]["openai_gpt_54_mini_cold"]["responses"]["temperature"] = 3
    write_config(config_path, payload)
    with pytest.raises(ValueError, match="temperature"):
        load_config(config_path)
