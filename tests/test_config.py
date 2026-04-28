import json
from pathlib import Path

import pytest

from curio import config as config_module
from curio.config import (
    ConfigError,
    CurioConfig,
    LlmCallerPromptConfig,
    TextifyConfig,
    TranslateConfig,
    load_config,
)
from curio.llm_caller import (
    CodexCliAuthConfig,
    CodexCliAuthMode,
    CodexCliReasoningEffort,
    CodexCliVerbosity,
    GoogleDocumentAiAuthConfig,
    GoogleDocumentAiProcessorKind,
    LlmPricing,
    OpenAiApiAuthConfig,
    OpenAiReasoningEffort,
    OpenAiTextVerbosity,
    ProviderName,
)
from curio.translate.adapter import (
    DEFAULT_TRANSLATION_INSTRUCTIONS,
    DEFAULT_TRANSLATION_USER_PROMPT_TEMPLATE,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def write_config(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def assert_default_translation_prompt_config(prompt_config: LlmCallerPromptConfig | None) -> None:
    assert prompt_config == LlmCallerPromptConfig(
        instructions=DEFAULT_TRANSLATION_INSTRUCTIONS,
        user=DEFAULT_TRANSLATION_USER_PROMPT_TEMPLATE,
    )


def test_config_path_points_to_current_working_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    assert config_module.config_path() == tmp_path / "config.json"


def test_checked_in_codex_example_config_parses() -> None:
    config = load_config(repo_root() / "config.example.codex_cli.json")
    caller_config = config.llm_caller_config("translator_codex_gpt_55")

    assert config.translate_config == TranslateConfig(llm_caller="translator_codex_gpt_54_mini")
    assert config.textify_config == TextifyConfig(llm_caller="textifier_codex_gpt_54_mini")
    assert caller_config.provider == ProviderName.CODEX_CLI
    assert caller_config.model == "gpt-5.5"
    assert caller_config.timeout_seconds == 300
    assert caller_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=5.0,
        cached_input_price_per_million=0.5,
        output_price_per_million=30.0,
    )
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
    assert_default_translation_prompt_config(caller_config.prompt_config)

    mini_config = config.llm_caller_config("translator_codex_gpt_54_mini")
    assert mini_config.model == "gpt-5.4-mini"
    assert mini_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0.75,
        cached_input_price_per_million=0.075,
        output_price_per_million=4.5,
    )
    assert mini_config.codex_exec_config is not None
    assert mini_config.codex_exec_config.model_verbosity == CodexCliVerbosity.LOW
    assert_default_translation_prompt_config(mini_config.prompt_config)

    gpt54_config = config.llm_caller_config("translator_codex_gpt_54")
    assert gpt54_config.model == "gpt-5.4"
    assert gpt54_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=2.5,
        cached_input_price_per_million=0.25,
        output_price_per_million=15.0,
    )
    assert gpt54_config.codex_exec_config is not None
    assert gpt54_config.codex_exec_config.model_reasoning_effort == CodexCliReasoningEffort.LOW
    assert gpt54_config.codex_exec_config.model_verbosity == CodexCliVerbosity.MEDIUM
    assert_default_translation_prompt_config(gpt54_config.prompt_config)

    textifier_config = config.llm_caller_config("textifier_codex_gpt_54_mini")
    assert textifier_config.provider == ProviderName.CODEX_CLI
    assert textifier_config.model == "gpt-5.4-mini"
    assert textifier_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0.75,
        cached_input_price_per_million=0.075,
        output_price_per_million=4.5,
    )
    assert textifier_config.prompt_config == LlmCallerPromptConfig(
        instructions="Return only JSON that satisfies the provided schema. Extract source-language text from the supplied local media.",
        user=textifier_config.prompt_config.user,
    )

    codex_textifier_config = config.llm_caller_config("textifier_codex_gpt_53_codex")
    assert codex_textifier_config.provider == ProviderName.CODEX_CLI
    assert codex_textifier_config.model == "gpt-5.3-codex"
    assert codex_textifier_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=1.75,
        cached_input_price_per_million=0.175,
        output_price_per_million=14.0,
    )
    assert codex_textifier_config.codex_exec_config is not None
    assert codex_textifier_config.codex_exec_config.model_reasoning_effort == CodexCliReasoningEffort.LOW
    assert codex_textifier_config.codex_exec_config.model_verbosity is None
    assert codex_textifier_config.prompt_config == textifier_config.prompt_config


def test_checked_in_openai_example_config_parses() -> None:
    config = load_config(repo_root() / "config.example.openai_api.json")
    caller_config = config.llm_caller_config("translator_openai_gpt_54_mini_cold")

    assert config.translate_config == TranslateConfig(llm_caller="translator_openai_gpt_54_mini_cold")
    assert caller_config.provider == ProviderName.OPENAI_API
    assert caller_config.model == "gpt-5.4-mini"
    assert caller_config.timeout_seconds == 300
    assert caller_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0.75,
        cached_input_price_per_million=0.075,
        output_price_per_million=4.5,
    )
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
    assert_default_translation_prompt_config(caller_config.prompt_config)

    gpt55_config = config.llm_caller_config("translator_openai_gpt_55")
    assert gpt55_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=5.0,
        cached_input_price_per_million=0.5,
        output_price_per_million=30.0,
    )
    assert_default_translation_prompt_config(gpt55_config.prompt_config)


def test_checked_in_google_document_ai_example_config_parses() -> None:
    config = load_config(repo_root() / "config.example.google_document_ai.json")
    caller_config = config.llm_caller_config("textifier_google_document_ai_layout")

    assert config.textify_config == TextifyConfig(llm_caller="textifier_google_document_ai_layout")
    assert caller_config.provider == ProviderName.GOOGLE_DOCUMENT_AI
    assert caller_config.model == "document-ai-layout-parser"
    assert caller_config.pricing_config == LlmPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0,
        cached_input_price_per_million=0,
        output_price_per_million=0,
        metered_price_per_thousand=10,
        metered_name="document_ai_pages",
        metered_unit="page",
    )
    assert isinstance(caller_config.auth_config, GoogleDocumentAiAuthConfig)
    assert caller_config.auth_config.processor_kind == GoogleDocumentAiProcessorKind.LAYOUT_PARSER


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
    with pytest.raises(ConfigError, match="llm_callers.translator_codex_gpt_55"):
        config.llm_caller_config("translator_codex_gpt_55")


def test_load_config_parses_optional_translate_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    del payload["translate"]
    write_config(config_path, payload)

    config = load_config(config_path)

    assert config.translate_config == TranslateConfig()
    assert config.textify_config == TextifyConfig(llm_caller="textifier_codex_gpt_54_mini")

    del payload["textify"]
    write_config(config_path, payload)
    config = load_config(config_path)
    assert config.textify_config == TextifyConfig()


def test_load_config_accepts_omitted_llm_caller_pricing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    del payload["llm_callers"]["translator_codex_gpt_55"]["pricing"]
    write_config(config_path, payload)

    config = load_config(config_path)

    assert config.llm_caller_config("translator_codex_gpt_55").pricing_config is None


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

    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    payload["textify"] = "bad"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="textify"):
        load_config(config_path)

    payload["textify"] = {"llm_caller": ""}
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="textify.llm_caller"):
        load_config(config_path)

    payload["textify"] = {"llm_caller": "missing_caller"}
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="llm_callers.missing_caller"):
        load_config(config_path)

    with pytest.raises(ConfigError, match="TextifyConfig"):
        CurioConfig(llm_callers={}, textify_config="bad")


def test_load_config_rejects_invalid_llm_caller_pricing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))

    payload["llm_callers"]["translator_codex_gpt_55"]["pricing"] = "bad"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="pricing"):
        load_config(config_path)

    payload["llm_callers"]["translator_codex_gpt_55"]["pricing"] = {
        "currency": "EUR",
        "basis": "api_equivalent",
        "input_price_per_million": 5.0,
        "cached_input_price_per_million": 0.5,
        "output_price_per_million": 30.0,
    }
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="pricing.currency"):
        load_config(config_path)

    payload["llm_callers"]["translator_codex_gpt_55"]["pricing"]["currency"] = "USD"
    payload["llm_callers"]["translator_codex_gpt_55"]["pricing"]["basis"] = "invoice"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="pricing.basis"):
        load_config(config_path)

    payload["llm_callers"]["translator_codex_gpt_55"]["pricing"]["basis"] = "api_equivalent"
    payload["llm_callers"]["translator_codex_gpt_55"]["pricing"]["input_price_per_million"] = -1
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="input_price_per_million"):
        load_config(config_path)

    payload = json.loads((repo_root() / "config.example.google_document_ai.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["textifier_google_document_ai_layout"]["pricing"]["metered_price_per_thousand"] = "free"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="metered_price_per_thousand"):
        load_config(config_path)


def test_load_config_parses_llm_caller_prompt_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["translator_codex_gpt_55"]["prompt"] = {
        "instructions": "Return {target_language} JSON for {request_id}",
        "user": "Translate {translation_request_json} with {output_schema_json} at {english_confidence_threshold}",
    }
    payload["llm_callers"]["textifier_codex_gpt_54_mini"]["prompt"] = {
        "user": "Textify {textify_request_json} {source_manifest_json} {preferred_output_format} {suggested_file_policy}"
    }
    payload["llm_callers"]["translator_codex_gpt_54_mini"]["prompt"] = {
        "instructions": "Only instructions {request_id}",
    }
    write_config(config_path, payload)

    config = load_config(config_path)

    assert config.llm_caller_config("translator_codex_gpt_55").prompt_config == LlmCallerPromptConfig(
        instructions="Return {target_language} JSON for {request_id}",
        user="Translate {translation_request_json} with {output_schema_json} at {english_confidence_threshold}",
    )
    assert config.llm_caller_config("translator_codex_gpt_54_mini").prompt_config == LlmCallerPromptConfig(
        instructions="Only instructions {request_id}",
    )
    assert config.llm_caller_config("textifier_codex_gpt_54_mini").prompt_config == LlmCallerPromptConfig(
        user="Textify {textify_request_json} {source_manifest_json} {preferred_output_format} {suggested_file_policy}"
    )


def test_load_config_rejects_invalid_llm_caller_prompt_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))

    payload["llm_callers"]["translator_codex_gpt_55"]["prompt"] = "bad"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="prompt"):
        load_config(config_path)

    payload["llm_callers"]["translator_codex_gpt_55"]["prompt"] = {"instructions": ""}
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="prompt.instructions"):
        load_config(config_path)

    invalid_templates = (
        ("{unknown}", "unsupported placeholder"),
        ("{request_id!r}", "format conversions"),
        ("{request_id:>10}", "format specs"),
        ("{", "valid Python format template"),
    )
    for template, message in invalid_templates:
        payload["llm_callers"]["translator_codex_gpt_55"]["prompt"] = {"user": template}
        write_config(config_path, payload)
        with pytest.raises(ConfigError, match=message):
            load_config(config_path)


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
                "translator_codex_gpt_55": {
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
    with pytest.raises(ConfigError, match="llm_callers.translator_codex_gpt_55.exec"):
        load_config(config_path)


def test_load_config_rejects_invalid_codex_exec_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.codex_cli.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["translator_codex_gpt_55"]["exec"]["extra_config"] = "bad"
    write_config(config_path, payload)

    with pytest.raises(ConfigError, match="extra_config"):
        load_config(config_path)

    payload["llm_callers"]["translator_codex_gpt_55"]["exec"]["extra_config"] = [""]
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="extra_config item"):
        load_config(config_path)

    payload["llm_callers"]["translator_codex_gpt_55"]["exec"]["extra_config"] = []
    payload["llm_callers"]["translator_codex_gpt_55"]["exec"]["ephemeral"] = "true"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="ephemeral"):
        load_config(config_path)


def test_load_config_rejects_invalid_named_caller_runtime_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    payload = json.loads((repo_root() / "config.example.openai_api.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["translator_openai_gpt_54_mini_cold"]["timeout_seconds"] = 0
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="timeout_seconds"):
        load_config(config_path)

    payload = json.loads((repo_root() / "config.example.openai_api.json").read_text(encoding="utf-8"))
    payload["llm_callers"]["translator_openai_gpt_54_mini_cold"]["responses"]["temperature"] = "cold"
    write_config(config_path, payload)
    with pytest.raises(ConfigError, match="temperature"):
        load_config(config_path)

    payload["llm_callers"]["translator_openai_gpt_54_mini_cold"]["responses"]["temperature"] = 3
    write_config(config_path, payload)
    with pytest.raises(ValueError, match="temperature"):
        load_config(config_path)
