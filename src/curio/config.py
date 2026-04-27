import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from string import Formatter
from typing import Any, cast

from curio.llm_caller.auth import (
    CodexCliAuthConfig,
    GoogleDocumentAiAuthConfig,
    OpenAiApiAuthConfig,
    ProviderAuthConfig,
)
from curio.llm_caller.codex_cli import CodexCliExecConfig
from curio.llm_caller.models import LlmPricing, ProviderName
from curio.llm_caller.openai_api import OpenAiResponsesConfig

JsonObject = dict[str, Any]
LLM_CALLER_PROMPT_TEMPLATE_FIELDS = frozenset(
    (
        "artifact_manifest_json",
        "preferred_output_format",
        "request_id",
        "suggested_file_policy",
        "textify_request_json",
        "output_schema_json",
        "translation_request_json",
        "target_language",
        "english_confidence_threshold",
    )
)


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LlmCallerPromptConfig:
    instructions: str | None = None
    user: str | None = None

    def __post_init__(self) -> None:
        if self.instructions is not None:
            _validate_prompt_template(self.instructions, "prompt.instructions")
        if self.user is not None:
            _validate_prompt_template(self.user, "prompt.user")


@dataclass(frozen=True, slots=True)
class LlmCallerConfig:
    name: str
    provider: ProviderName | str
    model: str
    auth_config: ProviderAuthConfig
    timeout_seconds: int
    prompt_config: LlmCallerPromptConfig | None = None
    pricing_config: LlmPricing | None = None
    codex_exec_config: CodexCliExecConfig | None = None
    openai_responses_config: OpenAiResponsesConfig | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", ProviderName(self.provider))
        _require_string(self.name, "llm_caller name")
        _require_string(self.model, "model")
        _require_positive_int(self.timeout_seconds, "timeout_seconds")


@dataclass(frozen=True, slots=True)
class TranslateConfig:
    llm_caller: str | None = None

    def __post_init__(self) -> None:
        if self.llm_caller is not None:
            _require_string(self.llm_caller, "translate.llm_caller")


@dataclass(frozen=True, slots=True)
class TextifyConfig:
    llm_caller: str | None = None

    def __post_init__(self) -> None:
        if self.llm_caller is not None:
            _require_string(self.llm_caller, "textify.llm_caller")


@dataclass(frozen=True, slots=True)
class CurioConfig:
    llm_callers: Mapping[str, LlmCallerConfig]
    translate_config: TranslateConfig = field(default_factory=TranslateConfig)
    textify_config: TextifyConfig = field(default_factory=TextifyConfig)

    def __post_init__(self) -> None:
        if not isinstance(self.translate_config, TranslateConfig):
            raise ConfigError("config.json must define 'translate' as a TranslateConfig")
        if not isinstance(self.textify_config, TextifyConfig):
            raise ConfigError("config.json must define 'textify' as a TextifyConfig")
        if (
            self.translate_config.llm_caller is not None
            and self.translate_config.llm_caller not in self.llm_callers
        ):
            raise ConfigError(f"config.json must define llm_callers.{self.translate_config.llm_caller}")
        if self.textify_config.llm_caller is not None and self.textify_config.llm_caller not in self.llm_callers:
            raise ConfigError(f"config.json must define llm_callers.{self.textify_config.llm_caller}")

    def llm_caller_config(self, name: str) -> LlmCallerConfig:
        caller_name = _require_string(name, "llm_caller")
        if caller_name not in self.llm_callers:
            raise ConfigError(f"config.json must define llm_callers.{caller_name}")
        return self.llm_callers[caller_name]


def config_path() -> Path:
    return Path.cwd() / "config.json"


def load_config(path: Path | None = None) -> CurioConfig:
    data = _load_config_data(path)
    callers_data = _require_mapping(data.get("llm_callers"), "llm_callers")
    llm_callers: dict[str, LlmCallerConfig] = {}
    for caller_key, caller_value in callers_data.items():
        caller_name = _require_string(caller_key, "llm_callers key")
        llm_callers[caller_name] = _parse_llm_caller_config(
            caller_name,
            _require_mapping(caller_value, f"llm_callers.{caller_name}"),
        )
    if not llm_callers:
        raise ConfigError("config.json must define at least one llm_caller")
    return CurioConfig(
        llm_callers=llm_callers,
        translate_config=_parse_translate_config(data.get("translate")),
        textify_config=_parse_textify_config(data.get("textify")),
    )


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


def _parse_llm_caller_config(name: str, data: Mapping[str, object]) -> LlmCallerConfig:
    path = f"llm_callers.{name}"
    provider = ProviderName(_require_string(data.get("provider"), f"{path}.provider"))
    auth_data = _require_mapping(data.get("auth"), f"{path}.auth")
    model = _require_string(data.get("model"), f"{path}.model")
    timeout_seconds = _require_positive_int(data.get("timeout_seconds"), f"{path}.timeout_seconds")
    prompt_config = _parse_prompt_config(data.get("prompt"), path)
    pricing_config = _parse_pricing_config(data.get("pricing"), path)
    if provider == ProviderName.OPENAI_API:
        return LlmCallerConfig(
            name=name,
            provider=provider,
            model=model,
            auth_config=OpenAiApiAuthConfig.from_json(auth_data),
            timeout_seconds=timeout_seconds,
            prompt_config=prompt_config,
            pricing_config=pricing_config,
            openai_responses_config=_parse_openai_responses_config(
                _require_mapping(data.get("responses"), f"{path}.responses"),
                path,
            ),
        )
    if provider == ProviderName.GOOGLE_DOCUMENT_AI:
        return LlmCallerConfig(
            name=name,
            provider=provider,
            model=model,
            auth_config=GoogleDocumentAiAuthConfig.from_json(auth_data),
            timeout_seconds=timeout_seconds,
            prompt_config=prompt_config,
            pricing_config=pricing_config,
        )
    return LlmCallerConfig(
        name=name,
        provider=provider,
        model=model,
        auth_config=CodexCliAuthConfig.from_json(auth_data),
        timeout_seconds=timeout_seconds,
        prompt_config=prompt_config,
        pricing_config=pricing_config,
        codex_exec_config=_parse_codex_exec_config(
            _require_mapping(data.get("exec"), f"{path}.exec"),
            path,
        ),
    )


def _parse_prompt_config(value: object, caller_path: str) -> LlmCallerPromptConfig | None:
    if value is None:
        return None
    data = _require_mapping(value, f"{caller_path}.prompt")
    return LlmCallerPromptConfig(
        instructions=_require_optional_string(data.get("instructions"), f"{caller_path}.prompt.instructions"),
        user=_require_optional_string(data.get("user"), f"{caller_path}.prompt.user"),
    )


def _parse_pricing_config(value: object, caller_path: str) -> LlmPricing | None:
    if value is None:
        return None
    data = _require_mapping(value, f"{caller_path}.pricing")
    currency = _require_string(data.get("currency"), f"{caller_path}.pricing.currency")
    if currency != "USD":
        raise ConfigError(f"config.json '{caller_path}.pricing.currency' must be USD")
    basis = _require_string(data.get("basis"), f"{caller_path}.pricing.basis")
    if basis != "api_equivalent":
        raise ConfigError(f"config.json '{caller_path}.pricing.basis' must be api_equivalent")
    return LlmPricing(
        currency=currency,
        basis=basis,
        input_price_per_million=_require_non_negative_number(
            data.get("input_price_per_million"),
            f"{caller_path}.pricing.input_price_per_million",
        ),
        cached_input_price_per_million=_require_non_negative_number(
            data.get("cached_input_price_per_million"),
            f"{caller_path}.pricing.cached_input_price_per_million",
        ),
        output_price_per_million=_require_non_negative_number(
            data.get("output_price_per_million"),
            f"{caller_path}.pricing.output_price_per_million",
        ),
        metered_price_per_thousand=_require_optional_non_negative_number(
            data.get("metered_price_per_thousand"),
            f"{caller_path}.pricing.metered_price_per_thousand",
        ),
        metered_name=_require_optional_string(data.get("metered_name"), f"{caller_path}.pricing.metered_name"),
        metered_unit=_require_optional_string(data.get("metered_unit"), f"{caller_path}.pricing.metered_unit"),
    )


def _parse_translate_config(value: object) -> TranslateConfig:
    if value is None:
        return TranslateConfig()
    data = _require_mapping(value, "translate")
    return TranslateConfig(
        llm_caller=_require_optional_string(data.get("llm_caller"), "translate.llm_caller"),
    )


def _parse_textify_config(value: object) -> TextifyConfig:
    if value is None:
        return TextifyConfig()
    data = _require_mapping(value, "textify")
    return TextifyConfig(
        llm_caller=_require_optional_string(data.get("llm_caller"), "textify.llm_caller"),
    )


def _parse_codex_exec_config(data: Mapping[str, object], caller_path: str) -> CodexCliExecConfig:
    exec_path = f"{caller_path}.exec"
    return CodexCliExecConfig(
        executable=_require_string(data.get("executable"), f"{exec_path}.executable"),
        sandbox=_require_string(data.get("sandbox"), f"{exec_path}.sandbox"),
        color=_require_string(data.get("color"), f"{exec_path}.color"),
        ephemeral=_require_bool(data.get("ephemeral"), f"{exec_path}.ephemeral"),
        json_events=_require_bool(data.get("json_events"), f"{exec_path}.json_events"),
        skip_git_repo_check=_require_bool(
            data.get("skip_git_repo_check"),
            f"{exec_path}.skip_git_repo_check",
        ),
        ignore_user_config=_require_bool(
            data.get("ignore_user_config"),
            f"{exec_path}.ignore_user_config",
        ),
        model_reasoning_effort=_require_optional_string(
            data.get("model_reasoning_effort"),
            f"{exec_path}.model_reasoning_effort",
        ),
        model_verbosity=_require_optional_string(data.get("model_verbosity"), f"{exec_path}.model_verbosity"),
        extra_config=[
            _require_string(override, f"{exec_path}.extra_config item")
            for override in _require_list(data.get("extra_config"), f"{exec_path}.extra_config")
        ],
    )


def _parse_openai_responses_config(data: Mapping[str, object], caller_path: str) -> OpenAiResponsesConfig:
    responses_path = f"{caller_path}.responses"
    return OpenAiResponsesConfig(
        temperature=_require_optional_number(data.get("temperature"), f"{responses_path}.temperature"),
        reasoning_effort=_require_optional_string(data.get("reasoning_effort"), f"{responses_path}.reasoning_effort"),
        max_output_tokens=_require_optional_positive_int(
            data.get("max_output_tokens"),
            f"{responses_path}.max_output_tokens",
        ),
        text_verbosity=_require_optional_string(data.get("text_verbosity"), f"{responses_path}.text_verbosity"),
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


def _require_optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, name)


def _require_positive_int(value: object, name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    raise ConfigError(f"config.json must define a positive integer '{name}'")


def _require_optional_positive_int(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _require_positive_int(value, name)


def _require_optional_number(value: object, name: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value
    raise ConfigError(f"config.json must define a numeric '{name}'")


def _require_non_negative_number(value: object, name: str) -> float | int:
    if isinstance(value, int | float) and not isinstance(value, bool) and value >= 0:
        return value
    raise ConfigError(f"config.json must define a non-negative numeric '{name}'")


def _require_optional_non_negative_number(value: object, name: str) -> float | int | None:
    if value is None:
        return None
    return _require_non_negative_number(value, name)


def _require_bool(value: object, name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"config.json must define a boolean '{name}'")


def _validate_prompt_template(value: object, name: str) -> str:
    template = _require_string(value, name)
    try:
        parsed_template = tuple(Formatter().parse(template))
    except ValueError as exc:
        raise ConfigError(f"config.json '{name}' must be a valid Python format template") from exc
    for _, field_name, format_spec, conversion in parsed_template:
        if field_name is None:
            continue
        if field_name not in LLM_CALLER_PROMPT_TEMPLATE_FIELDS:
            allowed = ", ".join(sorted(LLM_CALLER_PROMPT_TEMPLATE_FIELDS))
            raise ConfigError(f"config.json '{name}' uses unsupported placeholder '{field_name}'; allowed: {allowed}")
        if conversion is not None:
            raise ConfigError(f"config.json '{name}' must not use format conversions")
        if format_spec:
            raise ConfigError(f"config.json '{name}' must not use format specs")
    return template
