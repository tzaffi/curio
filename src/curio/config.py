import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from curio.llm_caller.auth import (
    CodexCliAuthConfig,
    OpenAiApiAuthConfig,
    ProviderAuthConfig,
)
from curio.llm_caller.codex_cli import CodexCliExecConfig
from curio.llm_caller.models import ProviderName

JsonObject = dict[str, Any]


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    auth_config: ProviderAuthConfig
    codex_exec_config: CodexCliExecConfig | None = None


@dataclass(frozen=True, slots=True)
class CurioConfig:
    providers: Mapping[ProviderName, ProviderConfig]

    def provider_config(self, provider: ProviderName | str) -> ProviderConfig:
        provider_name = ProviderName(provider)
        if provider_name not in self.providers:
            raise ConfigError(f"config.json must define providers.{provider_name.value}")
        return self.providers[provider_name]


def config_path() -> Path:
    return Path.cwd() / "config.json"


def load_config(path: Path | None = None) -> CurioConfig:
    data = _load_config_data(path)
    providers_data = _require_mapping(data.get("providers"), "providers")
    providers: dict[ProviderName, ProviderConfig] = {}
    for provider_key, provider_value in providers_data.items():
        provider_name = ProviderName(_require_string(provider_key, "providers key"))
        providers[provider_name] = _parse_provider_config(
            provider_name,
            _require_mapping(provider_value, f"providers.{provider_name.value}"),
        )
    if not providers:
        raise ConfigError("config.json must define at least one provider")
    return CurioConfig(providers=providers)


def _load_config_data(path: Path | None = None) -> JsonObject:
    resolved_path = config_path() if path is None else path
    if not resolved_path.exists():
        raise ConfigError(f"Missing config file at {resolved_path}")
    try:
        data = json.loads(resolved_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config.json must contain valid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config.json must contain a JSON object")
    return data


def _parse_provider_config(provider: ProviderName, data: Mapping[str, object]) -> ProviderConfig:
    auth_data = _require_mapping(data.get("auth"), f"providers.{provider.value}.auth")
    if provider == ProviderName.OPENAI_API:
        return ProviderConfig(auth_config=OpenAiApiAuthConfig.from_json(auth_data))
    return ProviderConfig(
        auth_config=CodexCliAuthConfig.from_json(auth_data),
        codex_exec_config=_parse_codex_exec_config(
            _require_mapping(data.get("exec"), "providers.codex_cli.exec")
        ),
    )


def _parse_codex_exec_config(data: Mapping[str, object]) -> CodexCliExecConfig:
    return CodexCliExecConfig(
        executable=_require_string(data.get("executable"), "providers.codex_cli.exec.executable"),
        sandbox=_require_string(data.get("sandbox"), "providers.codex_cli.exec.sandbox"),
        color=_require_string(data.get("color"), "providers.codex_cli.exec.color"),
        ephemeral=_require_bool(data.get("ephemeral"), "providers.codex_cli.exec.ephemeral"),
        json_events=_require_bool(data.get("json_events"), "providers.codex_cli.exec.json_events"),
        skip_git_repo_check=_require_bool(
            data.get("skip_git_repo_check"),
            "providers.codex_cli.exec.skip_git_repo_check",
        ),
        ignore_user_config=_require_bool(
            data.get("ignore_user_config"),
            "providers.codex_cli.exec.ignore_user_config",
        ),
        extra_config=[
            _require_string(override, "providers.codex_cli.exec.extra_config item")
            for override in _require_list(data.get("extra_config"), "providers.codex_cli.exec.extra_config")
        ],
    )


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return cast(Mapping[str, object], value)
    raise ConfigError(f"config.json must define '{name}' as an object")


def _require_list(value: object, name: str) -> list[object]:
    if isinstance(value, list):
        return cast(list[object], value)
    raise ConfigError(f"config.json must define '{name}' as a list")


def _require_string(value: object, name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise ConfigError(f"config.json must define a non-empty '{name}' string")


def _require_bool(value: object, name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"config.json must define a boolean '{name}'")
