import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from typer.testing import CliRunner

import curio.cli as cli
from curio.cli import app
from curio.config import LlmCallerPromptConfig, TranslateConfig
from curio.llm_caller import (
    LlmCostEstimate,
    LlmOutput,
    LlmProviderNotFoundError,
    LlmRequest,
    LlmResponse,
    LlmStatus,
    LlmUsage,
    MeteredObject,
    ProviderName,
)
from curio.translate import (
    Block,
    LlmSummary,
    TranslatedBlock,
    TranslationRequest,
    TranslationResponse,
)

runner = CliRunner()


class FakeCurioConfig:
    def __init__(
        self,
        llm_caller: str | None,
        prompt_configs: dict[str, LlmCallerPromptConfig | None] | None = None,
    ) -> None:
        self.translate_config = TranslateConfig(llm_caller=llm_caller)
        self.prompt_configs = {} if prompt_configs is None else dict(prompt_configs)

    def llm_caller_config(self, name: str) -> object:
        class FakeCallerConfig:
            def __init__(self, prompt_config: LlmCallerPromptConfig | None) -> None:
                self.prompt_config = prompt_config
                self.pricing_config = None

        return FakeCallerConfig(self.prompt_configs.get(name))


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=10,
        cached_input_tokens=None,
        output_tokens=4,
        reasoning_tokens=None,
        total_tokens=14,
        metered_objects=[MeteredObject(name="request", quantity=1, unit="count")],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:01Z",
        wall_seconds=1,
        thinking_seconds=None,
    )


class FakeTranslationService:
    def __init__(
        self,
        *,
        warnings: Sequence[str] = (),
        block_warnings: Sequence[str] = (),
        cost_estimate: LlmCostEstimate | None = None,
    ) -> None:
        self.requests: list[TranslationRequest] = []
        self.warnings = tuple(warnings)
        self.block_warnings = tuple(block_warnings)
        self.cost_estimate = cost_estimate

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        self.requests.append(request)
        return TranslationResponse(
            request_id=request.request_id,
            blocks=tuple(self._block_response(block) for block in request.blocks),
            llm=LlmSummary(
                provider=ProviderName.OPENAI_API if "openai" in (request.llm_caller or "") else ProviderName.CODEX_CLI,
                model=request.llm_caller,
                usage=make_usage(),
                cost_estimate=self.cost_estimate,
            ),
            warnings=self.warnings,
        )

    def _block_response(self, block: Block) -> TranslatedBlock:
        source_block = block
        source_language_hint = source_block.source_language_hint
        is_english = (
            source_language_hint is not None
            and source_language_hint.casefold().startswith("en")
            or source_block.text == "Already English."
        )
        return TranslatedBlock(
            block_id=source_block.block_id,
            name=source_block.name,
            detected_language=source_language_hint or ("en" if is_english else "fr"),
            english_confidence_estimate=0.99 if is_english else 0.01,
            translation_required=not is_english,
            translated_text=None if is_english else _fake_translation(source_block.text),
            warnings=self.block_warnings,
        )

def _fake_translation(text: str) -> str:
    if text.strip().casefold() == "bonjour":
        return "Hello"
    if text.strip() == "今日は新しいモデルを公開します。":
        return "Today we are releasing a new model."
    return f"Translated: {text.strip()}"


def install_fake_service(monkeypatch: pytest.MonkeyPatch, service: FakeTranslationService) -> None:
    monkeypatch.setattr(
        cli,
        "_build_translation_service",
        lambda _llm_caller, _config_path, config=None: service,
    )
    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini")


def install_fake_config(
    monkeypatch: pytest.MonkeyPatch,
    llm_caller: str | None,
    prompt_configs: dict[str, LlmCallerPromptConfig | None] | None = None,
) -> None:
    monkeypatch.setattr(cli, "load_config", lambda _path: FakeCurioConfig(llm_caller, prompt_configs))


class FakeLlmClient:
    def __init__(self, provider: ProviderName, model: str = "fake-model") -> None:
        self.provider = provider
        self.model = model
        self.requests: list[LlmRequest] = []

    def complete(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return LlmResponse(
            request_id=request.request_id,
            status=LlmStatus.SUCCEEDED,
            provider=self.provider,
            model=self.model,
            output=LlmOutput(
                value={
                    "request_id": request.request_id,
                    "blocks": [
                        {
                            "block_id": cli.RAW_CLI_BLOCK_ID,
                            "name": cli.RAW_CLI_BLOCK_NAME,
                            "detected_language": "fr",
                            "english_confidence_estimate": 0.01,
                            "translation_required": True,
                            "translated_text": "Hello",
                            "warnings": [],
                        }
                    ],
                }
            ),
            usage=make_usage(),
        )


def test_root_without_subcommand_shows_help() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "Semantic labeling of iMsgX artifacts" in result.output
    assert "translate" in result.output
    assert "curate" in result.output
    assert "bootstrap" in result.output
    assert "schema" in result.output
    assert "doctor" in result.output


def test_root_help_shows_reserved_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "translate" in result.output
    assert "curate" in result.output
    assert "bootstrap" in result.output
    assert "schema" in result.output
    assert "doctor" in result.output


def test_reserved_commands_report_stub_status() -> None:
    for command in ("curate", "bootstrap", "schema", "doctor"):
        result = runner.invoke(app, [command])

        assert result.exit_code == 1
        assert f"{command} is reserved but not implemented yet." in result.output


def test_cli_build_llm_caller_client_delegates_to_llm_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeLlmClient(ProviderName.CODEX_CLI)
    calls: list[tuple[str, object]] = []

    def fake_build_llm_caller_client(name: str, config: object, **kwargs: object) -> FakeLlmClient:
        del kwargs
        calls.append((name, config))
        return client

    monkeypatch.setattr(cli, "load_config", lambda path: f"loaded:{path}")
    monkeypatch.setattr(cli, "build_llm_caller_client", fake_build_llm_caller_client)

    assert cli._build_llm_caller_client("translator_openai_gpt_54_mini_cold", Path("curio-config.json")) is client
    assert calls == [("translator_openai_gpt_54_mini_cold", "loaded:curio-config.json")]


def test_translate_llm_caller_factory_errors_are_runtime_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_llm_caller_client_build(
        llm_caller: str,
        config_path: Path | None,
        config: object | None = None,
    ) -> FakeLlmClient:
        del config_path, config
        raise LlmProviderNotFoundError(f"llm caller client failed: {llm_caller}")

    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini")
    monkeypatch.setattr(cli, "_build_llm_caller_client", fail_llm_caller_client_build)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "bonjour"])

    assert result.exit_code == 1
    assert "llm caller client failed: translator_codex_gpt_55" in result.output


def test_translate_rejects_missing_llm_caller_for_raw_text(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    install_fake_config(monkeypatch, None)

    result = runner.invoke(app, ["translate", "bonjour"])

    assert result.exit_code == 2
    assert cli.LLM_CALLER_REQUIRED_MESSAGE in result.output
    assert service.requests == []


def test_translate_reports_config_load_error_when_default_caller_is_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    monkeypatch.setattr(cli, "load_config", lambda _path: (_ for _ in ()).throw(cli.ConfigError("bad config")))

    result = runner.invoke(app, ["translate", "bonjour"])

    assert result.exit_code == 1
    assert "bad config" in result.output
    assert service.requests == []


def test_request_llm_caller_rejects_unconfigured_request(capsys: pytest.CaptureFixture[str]) -> None:
    request = TranslationRequest(
        request_id="translate-without-llm-caller",
        blocks=[Block(block_id=1, name="message", source_language_hint=None, text="bonjour")],
    )

    with pytest.raises(cli.typer.Exit) as exc:
        cli._request_llm_caller(request)

    assert exc.value.exit_code == 2
    assert cli.LLM_CALLER_REQUIRED_MESSAGE in capsys.readouterr().err


def test_translate_default_service_uses_llm_caller_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeLlmClient(ProviderName.OPENAI_API)
    llm_callers: list[str] = []

    def fake_build_llm_caller_client(
        llm_caller: str,
        config_path: Path | None,
        config: object | None = None,
    ) -> FakeLlmClient:
        del config_path, config
        llm_callers.append(llm_caller)
        return client

    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini")
    monkeypatch.setattr(cli, "_build_llm_caller_client", fake_build_llm_caller_client)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_openai_gpt_54_mini_cold", "bonjour"])

    assert result.exit_code == 0
    assert result.output == "Hello\n"
    assert llm_callers == ["translator_openai_gpt_54_mini_cold"]
    assert client.requests[0].metadata["llm_caller"] == "translator_openai_gpt_54_mini_cold"


def test_translate_uses_configured_default_caller_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeLlmClient(ProviderName.CODEX_CLI)
    prompt_config = LlmCallerPromptConfig(
        instructions="Instructions {request_id} {target_language}",
        user="User {translation_request_json} {output_schema_json}",
    )

    install_fake_config(
        monkeypatch,
        "translator_codex_gpt_54_mini",
        {"translator_codex_gpt_54_mini": prompt_config},
    )
    monkeypatch.setattr(
        cli,
        "_build_llm_caller_client",
        lambda _llm_caller, _config_path, config=None: client,
    )

    result = runner.invoke(app, ["translate", "bonjour"])

    assert result.exit_code == 0
    assert client.requests[0].instructions.startswith("Instructions translate-")
    assert client.requests[0].instructions.endswith(" en")
    assert "User {" in client.requests[0].input[0].content[0].text
    assert '"text": "bonjour"' in client.requests[0].input[0].content[0].text
    assert '"translatedBlock"' in client.requests[0].input[0].content[0].text


def test_translate_cli_override_uses_override_caller_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeLlmClient(ProviderName.CODEX_CLI)
    prompt_configs = {
        "translator_codex_gpt_54_mini": LlmCallerPromptConfig(instructions="Default caller"),
        "translator_codex_gpt_55": LlmCallerPromptConfig(instructions="Override caller {target_language}"),
    }

    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini", prompt_configs)
    monkeypatch.setattr(
        cli,
        "_build_llm_caller_client",
        lambda _llm_caller, _config_path, config=None: client,
    )

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "bonjour"])

    assert result.exit_code == 0
    assert client.requests[0].instructions == "Override caller en"


def test_translate_json_caller_prompt_is_overridden_by_cli_prompt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client = FakeLlmClient(ProviderName.CODEX_CLI)
    prompt_configs = {
        "translator_openai_gpt_54_mini_cold": LlmCallerPromptConfig(instructions="JSON caller"),
        "translator_codex_gpt_55": LlmCallerPromptConfig(instructions="CLI caller"),
    }
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=cli.RAW_CLI_BLOCK_ID, name=cli.RAW_CLI_BLOCK_NAME, source_language_hint="fr", text="bonjour")],
        llm_caller="translator_openai_gpt_54_mini_cold",
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini", prompt_configs)
    monkeypatch.setattr(
        cli,
        "_build_llm_caller_client",
        lambda _llm_caller, _config_path, config=None: client,
    )

    json_result = runner.invoke(app, ["translate", "--input-json", str(input_path)])
    assert json_result.exit_code == 0
    assert client.requests[0].instructions == "JSON caller"
    client.requests.clear()
    override_result = runner.invoke(
        app,
        ["translate", "--input-json", str(input_path), "--llm-caller", "translator_codex_gpt_55"],
    )

    assert override_result.exit_code == 0
    assert client.requests[0].instructions == "CLI caller"


def test_build_translation_service_reuses_loaded_config(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeLlmClient(ProviderName.CODEX_CLI)
    prompt_config = LlmCallerPromptConfig(instructions="Helper prompt {target_language}")
    loaded_config = FakeCurioConfig(
        "translator_codex_gpt_54_mini",
        {"translator_codex_gpt_54_mini": prompt_config},
    )
    calls: list[tuple[str, Path | None, object | None]] = []

    def fake_build_llm_caller_client(
        llm_caller: str,
        config_path: Path | None,
        config: object | None = None,
    ) -> FakeLlmClient:
        calls.append((llm_caller, config_path, config))
        return client

    monkeypatch.setattr(cli, "_build_llm_caller_client", fake_build_llm_caller_client)

    service = cli._build_translation_service("translator_codex_gpt_54_mini", Path("curio-config.json"), config=loaded_config)

    assert service.llm_client is client
    assert calls == [("translator_codex_gpt_54_mini", Path("curio-config.json"), loaded_config)]
    assert service.prompt_config is prompt_config


def test_build_translation_service_loads_config_when_not_preloaded(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeLlmClient(ProviderName.CODEX_CLI)
    loaded_config = FakeCurioConfig("translator_codex_gpt_54_mini")

    def fake_build_llm_caller_client(
        llm_caller: str,
        config_path: Path | None,
        config: object | None = None,
    ) -> FakeLlmClient:
        assert llm_caller == "translator_codex_gpt_54_mini"
        assert config_path == Path("curio-config.json")
        assert config is loaded_config
        return client

    monkeypatch.setattr(cli, "load_config", lambda _path: loaded_config)
    monkeypatch.setattr(cli, "_build_llm_caller_client", fake_build_llm_caller_client)

    service = cli._build_translation_service("translator_codex_gpt_54_mini", Path("curio-config.json"))

    assert service.llm_client is client


def test_translate_raw_text_uses_injected_service_and_prints_translated_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(
        app,
        [
            "translate",
            "--llm-caller",
            "translator_openai_gpt_54_mini_cold",
            "--source-language",
            "fr",
            "--english-confidence-threshold",
            "0.75",
            "bonjour",
        ],
    )

    assert result.exit_code == 0
    assert result.output == "Hello\n"
    request = service.requests[0]
    assert request.llm_caller == "translator_openai_gpt_54_mini_cold"
    assert request.english_confidence_threshold == 0.75
    assert request.blocks[0].source_language_hint == "fr"
    assert request.blocks[0].text == "bonjour"


def test_translate_raw_text_uses_configured_default_llm_caller(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini")

    result = runner.invoke(app, ["translate", "bonjour"])

    assert result.exit_code == 0
    assert result.output == "Hello\n"
    assert service.requests[0].llm_caller == "translator_codex_gpt_54_mini"


def test_translate_raw_english_text_prints_original_text(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(
        app,
        ["translate", "--llm-caller", "translator_codex_gpt_55", "--source-language", "en-US", "Already English."],
    )

    assert result.exit_code == 0
    assert result.output == "Already English.\n"


def test_translate_raw_text_json_output_includes_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService(
        warnings=["provider warning"],
        block_warnings=["block warning"],
        cost_estimate=LlmCostEstimate("USD", "api_equivalent", 0.000026, 0.75, 0.075, 4.5),
    )
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "--json", "bonjour"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["translation_response_version"] == "curio-translation-response.v1"
    assert payload["warnings"] == ["provider warning"]
    assert payload["blocks"][0]["warnings"] == ["block warning"]
    assert payload["blocks"][0]["translated_text"] == "Hello"
    assert payload["llm"]["cost_estimate"]["amount"] == 0.000026


def test_translate_raw_text_non_json_emits_formatted_warnings_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService(warnings=["provider warning"], block_warnings=["block warning"])
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "bonjour"])

    assert result.exit_code == 0
    assert "[WARNINGS: provider warning]" in result.output
    assert "[WARNINGS: block warning]" in result.output
    assert "Hello" in result.output


def test_translate_raw_text_can_suppress_human_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService(warnings=["provider warning"], block_warnings=["block warning"])
    install_fake_service(monkeypatch, service)

    result = runner.invoke(
        app,
        ["translate", "--llm-caller", "translator_codex_gpt_55", "--suppress-warnings", "bonjour"],
    )

    assert result.exit_code == 0
    assert result.output == "Hello\n"


def test_translate_raw_text_stats_emits_usage_and_cost_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService(
        cost_estimate=LlmCostEstimate("USD", "api_equivalent", 0.000026, 0.75, 0.075, 4.5),
    )
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "--stats", "bonjour"])

    assert result.exit_code == 0
    assert "Hello\n" in result.output
    assert "[STATS: provider=codex_cli model=translator_codex_gpt_55" in result.output
    assert "input_tokens=10" in result.output
    assert "cached_input_tokens=unavailable" in result.output
    assert "output_tokens=4" in result.output
    assert "cost=USD 0.000026 (api_equivalent)" in result.output


def test_translate_raw_text_stats_reports_unavailable_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "--stats", "bonjour"])

    assert result.exit_code == 0
    assert "cost=unavailable" in result.output


def test_translate_reads_raw_text_from_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55"], input="bonjour\n")

    assert result.exit_code == 0
    assert result.output == "Hello\n"
    assert service.requests[0].blocks[0].text == "bonjour\n"


def test_stdin_reader_ignores_interactive_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    class TtyStdin:
        def isatty(self) -> bool:
            return True

        def read(self) -> str:
            raise AssertionError("interactive stdin must not be read")

    monkeypatch.setattr(cli.click, "get_text_stream", lambda _name: TtyStdin())

    assert cli._read_stdin_text() is None


def test_translate_reads_input_file_and_writes_output_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "note.txt"
    output_path = tmp_path / "translated.txt"
    input_path.write_text("bonjour", encoding="utf-8")

    result = runner.invoke(
        app,
        ["translate", "--llm-caller", "translator_codex_gpt_55", "--input-file", str(input_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert result.output == ""
    assert output_path.read_text(encoding="utf-8") == "Hello\n"


def test_translate_reads_structured_input_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[
            Block(
                block_id=1,
                name="message",
                source_language_hint="ja",
                text="今日は新しいモデルを公開します。",
            )
        ],
        llm_caller="translator_openai_gpt_54_mini_cold",
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(app, ["translate", "--input-json", str(input_path)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["request_id"] == "translate-from-json"
    assert payload["blocks"][0]["translated_text"] == "Today we are releasing a new model."
    assert service.requests[0].llm_caller == "translator_openai_gpt_54_mini_cold"


def test_translate_structured_input_uses_configured_default_llm_caller(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    install_fake_config(monkeypatch, "translator_codex_gpt_54_mini")
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=1, name="message", source_language_hint="fr", text="bonjour")],
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(app, ["translate", "--input-json", str(input_path)])

    assert result.exit_code == 0
    assert service.requests[0].llm_caller == "translator_codex_gpt_54_mini"


def test_translate_structured_input_accepts_cli_llm_caller_when_request_omits_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=1, name="message", source_language_hint="fr", text="bonjour")],
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "translate",
            "--input-json",
            str(input_path),
            "--llm-caller",
            "translator_codex_gpt_55",
            "--english-confidence-threshold",
            "0.5",
        ],
    )

    assert result.exit_code == 0
    request = service.requests[0]
    assert request.llm_caller == "translator_codex_gpt_55"
    assert request.english_confidence_threshold == 0.5


def test_translate_structured_input_lets_cli_llm_caller_override_json_llm_caller(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=1, name="message", source_language_hint="fr", text="bonjour")],
        llm_caller="translator_openai_gpt_54_mini_cold",
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "translate",
            "--input-json",
            str(input_path),
            "--llm-caller",
            "translator_codex_gpt_55",
        ],
    )

    assert result.exit_code == 0
    assert service.requests[0].llm_caller == "translator_codex_gpt_55"


def test_translate_rejects_ambiguous_and_missing_input_modes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "note.txt"
    input_path.write_text("bonjour", encoding="utf-8")

    ambiguous = runner.invoke(
        app,
        ["translate", "--llm-caller", "translator_codex_gpt_55", "--input-file", str(input_path), "bonjour"],
    )
    missing = runner.invoke(app, ["translate"])

    assert ambiguous.exit_code == 2
    assert missing.exit_code == 2
    assert "exactly one input mode" in ambiguous.output
    assert "exactly one input mode" in missing.output
    assert service.requests == []


def test_translate_rejects_source_language_with_input_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=1, name="message", source_language_hint="fr", text="bonjour")],
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(app, ["translate", "--input-json", str(input_path), "--source-language", "fr"])

    assert result.exit_code == 2
    assert "--source-language can only be used with raw text input" in result.output
    assert service.requests == []


def test_translate_rejects_structured_input_without_llm_caller(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    install_fake_config(monkeypatch, None)
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=1, name="message", source_language_hint="fr", text="bonjour")],
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(app, ["translate", "--input-json", str(input_path)])

    assert result.exit_code == 2
    assert cli.LLM_CALLER_REQUIRED_MESSAGE in result.output
    assert service.requests == []


def test_translate_reports_invalid_input_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "request.json"
    input_path.write_text("{", encoding="utf-8")

    result = runner.invoke(app, ["translate", "--input-json", str(input_path)])

    assert result.exit_code == 2
    assert "--input-json must contain valid JSON" in result.output


def test_translate_reports_unreadable_input_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "missing.txt"

    result = runner.invoke(app, ["translate", "--input-file", str(input_path)])

    assert result.exit_code == 2
    assert "could not read --input-file" in result.output


def test_translate_rejects_invalid_request_options(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    target_language = runner.invoke(
        app,
        ["translate", "--llm-caller", "translator_codex_gpt_55", "--target-language", "fr", "bonjour"],
    )
    llm_caller = runner.invoke(app, ["translate", "--llm-caller", "", "bonjour"])

    assert target_language.exit_code == 2
    assert llm_caller.exit_code == 2
    assert "target_language must be en" in target_language.output
    assert "llm_caller must not be empty" in llm_caller.output
    assert service.requests == []


def test_translate_reports_output_write_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--llm-caller", "translator_codex_gpt_55", "--output", str(tmp_path), "bonjour"])

    assert result.exit_code == 1
    assert "could not write --output" in result.output
