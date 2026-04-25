import json
from collections.abc import Sequence
from pathlib import Path

import pytest
from typer.testing import CliRunner

import curio.cli as cli
from curio.cli import app
from curio.llm_caller import LlmUsage, MeteredObject, ProviderName
from curio.translate import (
    Block,
    LlmSummary,
    TranslatedBlock,
    TranslationRequest,
    TranslationResponse,
)

runner = CliRunner()


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
    ) -> None:
        self.requests: list[TranslationRequest] = []
        self.warnings = tuple(warnings)
        self.block_warnings = tuple(block_warnings)

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        self.requests.append(request)
        return TranslationResponse(
            request_id=request.request_id,
            blocks=tuple(self._block_response(block) for block in request.blocks),
            llm=LlmSummary(
                provider=request.provider or ProviderName.CODEX_CLI,
                model=request.model,
                usage=make_usage(),
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
    monkeypatch.setattr(cli, "_build_translation_service", lambda: service)


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


def test_translate_without_provider_client_reports_runtime_error() -> None:
    result = runner.invoke(app, ["translate", "bonjour"])

    assert result.exit_code == 1
    assert "provider client is not implemented yet: codex_cli" in result.output


def test_translate_raw_text_uses_injected_service_and_prints_translated_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(
        app,
        [
            "translate",
            "--provider",
            "openai_api",
            "--model",
            "gpt-test",
            "--timeout-seconds",
            "42",
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
    assert request.provider == ProviderName.OPENAI_API
    assert request.model == "gpt-test"
    assert request.timeout_seconds == 42
    assert request.english_confidence_threshold == 0.75
    assert request.blocks[0].source_language_hint == "fr"
    assert request.blocks[0].text == "bonjour"


def test_translate_raw_english_text_prints_original_text(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--source-language", "en-US", "Already English."])

    assert result.exit_code == 0
    assert result.output == "Already English.\n"


def test_translate_raw_text_json_output_includes_warnings(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService(warnings=["provider warning"], block_warnings=["block warning"])
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--json", "bonjour"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["translation_response_version"] == "curio-translation-response.v1"
    assert payload["warnings"] == ["provider warning"]
    assert payload["blocks"][0]["warnings"] == ["block warning"]
    assert payload["blocks"][0]["translated_text"] == "Hello"


def test_translate_raw_text_non_json_emits_warnings_to_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService(warnings=["provider warning"], block_warnings=["block warning"])
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "bonjour"])

    assert result.exit_code == 0
    assert "provider warning" in result.output
    assert "block warning" in result.output
    assert "Hello" in result.output


def test_translate_reads_raw_text_from_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate"], input="bonjour\n")

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

    result = runner.invoke(app, ["translate", "--input-file", str(input_path), "--output", str(output_path)])

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
        provider="openai_api",
        model="json-model",
        timeout_seconds=45,
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(app, ["translate", "--input-json", str(input_path)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["request_id"] == "translate-from-json"
    assert payload["blocks"][0]["translated_text"] == "Today we are releasing a new model."
    assert service.requests[0].provider == ProviderName.OPENAI_API
    assert service.requests[0].model == "json-model"
    assert service.requests[0].timeout_seconds == 45


def test_translate_structured_input_accepts_cli_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "request.json"
    request = TranslationRequest(
        request_id="translate-from-json",
        blocks=[Block(block_id=1, name="message", source_language_hint="fr", text="bonjour")],
        provider="openai_api",
        model="json-model",
        timeout_seconds=45,
    )
    input_path.write_text(json.dumps(request.to_json()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "translate",
            "--input-json",
            str(input_path),
            "--provider",
            "codex_cli",
            "--model",
            "cli-model",
            "--timeout-seconds",
            "9",
            "--english-confidence-threshold",
            "0.5",
        ],
    )

    assert result.exit_code == 0
    request = service.requests[0]
    assert request.provider == ProviderName.CODEX_CLI
    assert request.model == "cli-model"
    assert request.timeout_seconds == 9
    assert request.english_confidence_threshold == 0.5


def test_translate_rejects_ambiguous_and_missing_input_modes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)
    input_path = tmp_path / "note.txt"
    input_path.write_text("bonjour", encoding="utf-8")

    ambiguous = runner.invoke(app, ["translate", "--input-file", str(input_path), "bonjour"])
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

    target_language = runner.invoke(app, ["translate", "--target-language", "fr", "bonjour"])
    provider = runner.invoke(app, ["translate", "--provider", "bogus", "bonjour"])

    assert target_language.exit_code == 2
    assert provider.exit_code == 2
    assert "target_language must be en" in target_language.output
    assert "bogus" in provider.output
    assert service.requests == []


def test_translate_reports_output_write_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service = FakeTranslationService()
    install_fake_service(monkeypatch, service)

    result = runner.invoke(app, ["translate", "--output", str(tmp_path), "bonjour"])

    assert result.exit_code == 1
    assert "could not write --output" in result.output
