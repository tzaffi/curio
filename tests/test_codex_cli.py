import json
from pathlib import Path
from typing import cast

import pytest

import curio.llm_caller.codex_cli as codex_cli
from curio.llm_caller import (
    CODEX_CLI_CAPABILITIES,
    CodexCliAuthConfig,
    CodexCliAuthMode,
    CodexCliClient,
    CodexCliCommand,
    CodexCliExecConfig,
    CodexCliRunner,
    CodexCliRunResult,
    JsonSchemaOutput,
    LlmConfigurationError,
    LlmInvalidOutputError,
    LlmMessage,
    LlmMessageRole,
    LlmProviderNotFoundError,
    LlmRejectedRequestError,
    LlmRequest,
    LlmSchemaValidationError,
    LlmTimeoutError,
    ProviderCallTiming,
    ProviderName,
    SubprocessCodexCliRunner,
    TextContentPart,
    UnsupportedCapabilityError,
    build_codex_exec_command,
    build_codex_exec_prompt,
    build_codex_llm_response,
    parse_codex_exec_jsonl,
)


def make_request(model: str | None = "gpt-test", output_schema: dict[str, object] | None = None) -> LlmRequest:
    return LlmRequest(
        request_id="translate-test",
        workflow="translate",
        model=model,
        instructions="Return translated blocks as JSON.",
        input=[
            LlmMessage(role="system", content=[TextContentPart(text="System context.")]),
            LlmMessage(role="user", content=[TextContentPart(text="Bonjour."), TextContentPart(text="Salut.")]),
        ],
        output=JsonSchemaOutput(
            name="curio_translation_model_output",
            schema={"type": "object"} if output_schema is None else output_schema,
        ),
        required_capabilities=["text_generation", "json_schema_output"],
        timeout_seconds=120,
        metadata={},
    )


def make_timing() -> ProviderCallTiming:
    return ProviderCallTiming(
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:03Z",
        wall_seconds=3,
    )


def jsonl(*events: object) -> str:
    return "\n".join(json.dumps(event) for event in events) + "\n"


class FakeCodexCliRunner:
    def __init__(
        self,
        stdout: str = "",
        *,
        stderr: str = "",
        return_code: int = 0,
        exception: Exception | None = None,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.exception = exception
        self.calls: list[tuple[CodexCliCommand, int]] = []
        self.schema_path: Path | None = None
        self.schema_payload: object | None = None

    def run(self, command: CodexCliCommand, timeout_seconds: int) -> CodexCliRunResult:
        self.calls.append((command, timeout_seconds))
        self.schema_path = Path(command.argv[command.argv.index("--output-schema") + 1])
        self.schema_payload = json.loads(self.schema_path.read_text(encoding="utf-8"))
        if self.exception is not None:
            raise self.exception
        return CodexCliRunResult(
            stdout=self.stdout,
            stderr=self.stderr,
            return_code=self.return_code,
            timing=make_timing(),
        )


def make_client(
    runner: CodexCliRunner,
    tmp_path: Path,
    *,
    auth_config: CodexCliAuthConfig | None = None,
    exec_config: CodexCliExecConfig | None = None,
    default_model: str | None = None,
) -> CodexCliClient:
    return CodexCliClient(
        runner=runner,
        exec_config=CodexCliExecConfig() if exec_config is None else exec_config,
        auth_config=CodexCliAuthConfig() if auth_config is None else auth_config,
        working_directory=tmp_path,
        output_schema_dir=tmp_path,
        default_model=default_model,
    )


def test_build_codex_exec_command_uses_stdin_prompt_and_safe_defaults() -> None:
    request = make_request()
    command = build_codex_exec_command(
        request,
        output_schema_path=Path("/tmp/curio-output.schema.json"),
        working_directory=Path("/Users/zeph/github/tzaffi/curio"),
        config=CodexCliExecConfig(
            skip_git_repo_check=True,
            ignore_user_config=True,
            extra_config=["model_reasoning_effort=low"],
        ),
    )

    assert command.argv == (
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--output-schema",
        "/tmp/curio-output.schema.json",
        "--cd",
        "/Users/zeph/github/tzaffi/curio",
        "--config",
        "model_reasoning_effort=low",
        "--model",
        "gpt-test",
        "-",
    )
    assert command.stdin_text == build_codex_exec_prompt(request)
    assert "Request ID: translate-test" in command.stdin_text
    assert "Workflow: translate" in command.stdin_text
    assert "<message role=system>" in command.stdin_text
    assert "Bonjour.\nSalut." in command.stdin_text
    assert "--output-schema" in command.stdin_text


def test_build_codex_exec_command_accepts_minimal_config_without_model() -> None:
    command = build_codex_exec_command(
        make_request(model=None),
        output_schema_path=Path("schema.json"),
        config=CodexCliExecConfig(json_events=False, ephemeral=False),
        working_directory=Path("/Users/zeph/github/tzaffi/curio"),
    )

    assert command.argv == (
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--output-schema",
        "schema.json",
        "--cd",
        "/Users/zeph/github/tzaffi/curio",
        "-",
    )

    with pytest.raises(ValueError, match="working_directory must be a path"):
        build_codex_exec_command(
            make_request(model=None),
            output_schema_path=Path("schema.json"),
            config=CodexCliExecConfig(),
            working_directory=cast(Path, None),
        )


def test_codex_exec_config_rejects_empty_values() -> None:
    with pytest.raises(ValueError, match="executable must not be empty"):
        CodexCliExecConfig(executable=" ")

    with pytest.raises(ValueError, match="sandbox must be a string"):
        CodexCliExecConfig(sandbox=cast(str, None))

    with pytest.raises(ValueError, match="config override must not be empty"):
        CodexCliExecConfig(extra_config=[""])


def test_parse_codex_exec_jsonl_extracts_final_agent_message_usage_and_warnings() -> None:
    output = jsonl(
        {"type": "thread.started", "thread_id": "thread-test"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "item_0", "type": "error", "message": "provider warning"}},
        {
            "type": "item.completed",
            "item": {
                "id": "item_1",
                "type": "agent_message",
                "text": json.dumps({"translated_blocks": [{"block_id": 1, "text": "Hello."}]}),
            },
        },
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 20,
                "cached_input_tokens": 5,
                "output_tokens": 7,
                "reasoning_output_tokens": 2,
            },
        },
    )

    result = parse_codex_exec_jsonl(output)

    assert result.output_value == {"translated_blocks": [{"block_id": 1, "text": "Hello."}]}
    assert result.usage_input_tokens == 20
    assert result.usage_cached_input_tokens == 5
    assert result.usage_output_tokens == 7
    assert result.usage_reasoning_tokens == 2
    assert result.usage_total_tokens == 27
    assert result.warnings == ("provider warning",)

    response = build_codex_llm_response(make_request(), result, make_timing())
    assert response.provider == ProviderName.CODEX_CLI
    assert response.model == "gpt-test"
    assert response.output is not None
    assert response.output.value == result.output_value
    assert response.usage.wall_seconds == 3
    assert response.usage.total_tokens == 27
    assert response.warnings == ("provider warning",)


def test_parse_codex_exec_jsonl_accepts_compatibility_event_shapes() -> None:
    output = jsonl(
        {
            "type": "item.completed",
            "item": {
                "id": "item_0",
                "item_type": "assistant_message",
                "text": json.dumps({"older": "shape"}),
            },
        },
        {"type": "agent_message", "message": json.dumps({"direct": "message"})},
        {"type": "task_complete", "last_agent_message": json.dumps({"final": "message"})},
        {
            "type": "token_count",
            "info": {
                "last_token_usage": {
                    "input_tokens": 3,
                    "cached_input_tokens": 1,
                    "output_tokens": 4,
                    "total_tokens": 7,
                }
            },
        },
    )

    result = parse_codex_exec_jsonl(output)

    assert result.output_value == {"final": "message"}
    assert result.usage_input_tokens == 3
    assert result.usage_cached_input_tokens == 1
    assert result.usage_output_tokens == 4
    assert result.usage_reasoning_tokens is None
    assert result.usage_total_tokens == 7


def test_parse_codex_exec_jsonl_allows_missing_usage() -> None:
    result = parse_codex_exec_jsonl("\n" + jsonl({"type": "agent_message", "text": "{}"}))

    assert result.output_value == {}
    assert result.usage_input_tokens is None
    assert result.usage_output_tokens is None
    assert result.usage_total_tokens is None


def test_parse_codex_exec_jsonl_reports_invalid_events() -> None:
    with pytest.raises(LlmInvalidOutputError, match="line 1 is not valid JSON"):
        parse_codex_exec_jsonl("{")

    with pytest.raises(LlmInvalidOutputError, match="line 1 must be an object"):
        parse_codex_exec_jsonl(json.dumps([]))

    with pytest.raises(LlmInvalidOutputError, match="event is missing type"):
        parse_codex_exec_jsonl(jsonl({"item": {}}))

    with pytest.raises(LlmInvalidOutputError, match="string field must be a string"):
        parse_codex_exec_jsonl(jsonl({"type": 1}))

    with pytest.raises(LlmInvalidOutputError, match="item.completed event is missing item"):
        parse_codex_exec_jsonl(jsonl({"type": "item.completed"}))

    with pytest.raises(LlmInvalidOutputError, match="field must be an object"):
        parse_codex_exec_jsonl(jsonl({"type": "item.completed", "item": "bad"}))

    with pytest.raises(LlmInvalidOutputError, match="agent message must not be empty"):
        parse_codex_exec_jsonl(jsonl({"type": "agent_message", "text": " "}))

    with pytest.raises(LlmInvalidOutputError, match="did not include a final agent message"):
        parse_codex_exec_jsonl(jsonl({"type": "turn.completed", "usage": {}}))

    with pytest.raises(LlmInvalidOutputError, match="final agent message is not valid JSON"):
        parse_codex_exec_jsonl(jsonl({"type": "agent_message", "text": "not json"}))

    with pytest.raises(LlmInvalidOutputError, match="input_tokens must be a non-negative number"):
        parse_codex_exec_jsonl(
            jsonl(
                {"type": "agent_message", "text": "{}"},
                {"type": "turn.completed", "usage": {"input_tokens": -1}},
            )
        )

    with pytest.raises(LlmInvalidOutputError, match="output_tokens must be a non-negative number"):
        parse_codex_exec_jsonl(
            jsonl(
                {"type": "agent_message", "text": "{}"},
                {"type": "turn.completed", "usage": {"output_tokens": True}},
            )
        )


def test_parse_codex_exec_jsonl_handles_error_items_without_messages_and_empty_token_count() -> None:
    result = parse_codex_exec_jsonl(
        jsonl(
            {"type": "item.completed", "item": {"type": "error"}},
            {"type": "token_count"},
            {"type": "agent_message", "text": "{}"},
        )
    )

    assert result.output_value == {}
    assert result.warnings == ("codex_cli emitted an error item",)
    assert result.usage_total_tokens is None


def test_build_codex_llm_response_accepts_model_override() -> None:
    result = parse_codex_exec_jsonl(
        jsonl(
            {"type": "agent_message", "text": "{}"},
            {"type": "turn.completed", "usage": {"total_tokens": 0}},
        )
    )

    response = build_codex_llm_response(make_request(), result, make_timing(), model="codex-model")

    assert response.model == "codex-model"
    assert response.usage.total_tokens == 0
    assert response.status.value == "succeeded"
    assert response.output is not None
    assert isinstance(response.output.value, dict)
    assert response.output.value == {}
    assert response.usage.metered_objects == ()
    assert response.usage.thinking_seconds is None
    assert response.usage.input_tokens is None
    assert response.usage.output_tokens is None
    assert response.usage.cached_input_tokens is None
    assert response.usage.reasoning_tokens is None
    assert response.request_id == "translate-test"
    assert response.provider == ProviderName.CODEX_CLI
    assert make_request().input[0].role == LlmMessageRole.SYSTEM


def test_codex_cli_client_calls_fake_runner_and_validates_schema(tmp_path: Path) -> None:
    output_schema = {
        "type": "object",
        "required": ["ok"],
        "properties": {"ok": {"type": "boolean"}},
        "additionalProperties": False,
    }
    runner = FakeCodexCliRunner(
        stdout=jsonl(
            {"type": "agent_message", "text": json.dumps({"ok": True})},
            {"type": "turn.completed", "usage": {"input_tokens": 6, "output_tokens": 2, "total_tokens": 8}},
        )
    )
    client = make_client(runner, tmp_path, default_model="codex-default")

    response = client.complete(make_request(model=None, output_schema=output_schema))

    assert runner.schema_payload == output_schema
    assert runner.schema_path is not None
    assert not runner.schema_path.exists()
    assert len(runner.calls) == 1
    command, timeout_seconds = runner.calls[0]
    assert timeout_seconds == 120
    assert "--model" in command.argv
    assert command.argv[command.argv.index("--model") + 1] == "codex-default"
    assert command.argv[-1] == "-"
    assert response.provider == ProviderName.CODEX_CLI
    assert response.model == "codex-default"
    assert response.output is not None
    assert response.output.value == {"ok": True}
    assert response.usage.total_tokens == 8


def test_codex_cli_client_uses_chatgpt_cached_auth_without_curio_secret(tmp_path: Path) -> None:
    runner = FakeCodexCliRunner(stdout=jsonl({"type": "agent_message", "text": "{}"}))
    client = make_client(runner, tmp_path, auth_config=CodexCliAuthConfig(mode=CodexCliAuthMode.CHATGPT))

    response = client.complete(make_request())

    assert len(runner.calls) == 1
    assert response.output is not None
    assert response.output.value == {}


def test_codex_cli_client_rejects_unsupported_capabilities_before_runner(tmp_path: Path) -> None:
    runner = FakeCodexCliRunner(stdout=jsonl({"type": "agent_message", "text": "{}"}))
    client = make_client(runner, tmp_path)
    request = LlmRequest(
        request_id="translate-test",
        workflow="translate",
        model=None,
        instructions="Return JSON.",
        input=[LlmMessage(role="user", content=[TextContentPart(text="hi")])],
        output=JsonSchemaOutput(name="output", schema={"type": "object"}),
        required_capabilities=["thinking_time"],
    )

    with pytest.raises(UnsupportedCapabilityError, match="thinking_time"):
        client.complete(request)

    assert runner.calls == []
    assert CODEX_CLI_CAPABILITIES == client.capabilities


def test_codex_cli_client_requires_model_before_runner(tmp_path: Path) -> None:
    runner = FakeCodexCliRunner(stdout=jsonl({"type": "agent_message", "text": "{}"}))
    client = make_client(runner, tmp_path)

    with pytest.raises(LlmConfigurationError, match="model is required"):
        client.complete(make_request(model=None))

    assert runner.calls == []


def test_codex_cli_client_keeps_api_key_handoff_isolated_before_runner(tmp_path: Path) -> None:
    runner = FakeCodexCliRunner(stdout=jsonl({"type": "agent_message", "text": "{}"}))
    client = make_client(runner, tmp_path, auth_config=CodexCliAuthConfig(mode=CodexCliAuthMode.API_KEY))

    with pytest.raises(LlmConfigurationError, match="API-key handoff is not implemented"):
        client.complete(make_request())

    assert runner.calls == []


def test_codex_cli_client_maps_runner_failures_and_exit_status(tmp_path: Path) -> None:
    missing_runner = FakeCodexCliRunner(exception=FileNotFoundError("missing codex"))
    missing_client = make_client(missing_runner, tmp_path)
    with pytest.raises(LlmProviderNotFoundError, match="codex_cli executable not found"):
        missing_client.complete(make_request())
    assert len(missing_runner.calls) == 1

    timeout_runner = FakeCodexCliRunner(exception=TimeoutError("slow codex"))
    timeout_client = make_client(timeout_runner, tmp_path)
    with pytest.raises(LlmTimeoutError, match="codex_cli subprocess timed out"):
        timeout_client.complete(make_request())
    assert len(timeout_runner.calls) == 1

    failed_runner = FakeCodexCliRunner(stderr="secret-ish stderr", return_code=7)
    failed_client = make_client(failed_runner, tmp_path)
    with pytest.raises(LlmRejectedRequestError) as failed:
        failed_client.complete(make_request())
    assert str(failed.value) == "codex_cli subprocess exited with status 7"
    assert "secret-ish" not in str(failed.value)


def test_codex_cli_client_reports_invalid_or_schema_invalid_output(tmp_path: Path) -> None:
    invalid_runner = FakeCodexCliRunner(stdout=jsonl({"type": "agent_message", "text": "not json"}))
    invalid_client = make_client(invalid_runner, tmp_path)
    with pytest.raises(LlmInvalidOutputError, match="final agent message is not valid JSON"):
        invalid_client.complete(make_request())

    schema_runner = FakeCodexCliRunner(stdout=jsonl({"type": "agent_message", "text": json.dumps({"ok": "yes"})}))
    schema_client = make_client(schema_runner, tmp_path)
    with pytest.raises(LlmSchemaValidationError, match="output did not match requested schema"):
        schema_client.complete(
            make_request(
                output_schema={
                    "type": "object",
                    "required": ["ok"],
                    "properties": {"ok": {"type": "boolean"}},
                }
            )
        )


def test_codex_cli_run_result_rejects_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="stdout must be a string"):
        CodexCliRunResult(stdout=cast(str, None), stderr="", return_code=0, timing=make_timing())

    with pytest.raises(ValueError, match="stderr must be a string"):
        CodexCliRunResult(stdout="", stderr=cast(str, None), return_code=0, timing=make_timing())

    with pytest.raises(ValueError, match="return_code must be an integer"):
        CodexCliRunResult(stdout="", stderr="", return_code=True, timing=make_timing())


def test_subprocess_codex_cli_runner_uses_command_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    command = CodexCliCommand(argv=("codex", "exec", "-"), stdin_text="prompt")

    def fake_run(
        argv: tuple[str, ...],
        *,
        input: str,
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> codex_cli.subprocess.CompletedProcess[str]:
        assert argv == command.argv
        assert input == "prompt"
        assert capture_output is True
        assert text is True
        assert timeout == 5
        assert check is False
        return codex_cli.subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout=jsonl({"type": "agent_message", "text": "{}"}),
            stderr="",
        )

    monkeypatch.setattr(codex_cli.subprocess, "run", fake_run)

    result = SubprocessCodexCliRunner().run(command, timeout_seconds=5)

    assert result.return_code == 0
    assert result.stderr == ""
    assert result.stdout == jsonl({"type": "agent_message", "text": "{}"})
    assert result.timing.wall_seconds >= 0


def test_subprocess_codex_cli_runner_maps_subprocess_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    command = CodexCliCommand(argv=("codex", "exec", "-"), stdin_text="prompt")

    def raise_missing(**kwargs: object) -> None:
        del kwargs
        raise FileNotFoundError("missing")

    monkeypatch.setattr(codex_cli.subprocess, "run", lambda *args, **kwargs: raise_missing(**kwargs))
    with pytest.raises(LlmProviderNotFoundError, match="codex_cli executable not found"):
        SubprocessCodexCliRunner().run(command, timeout_seconds=5)

    def raise_timeout(**kwargs: object) -> None:
        del kwargs
        raise codex_cli.subprocess.TimeoutExpired(cmd=command.argv, timeout=5)

    monkeypatch.setattr(codex_cli.subprocess, "run", lambda *args, **kwargs: raise_timeout(**kwargs))
    with pytest.raises(LlmTimeoutError, match="codex_cli subprocess timed out"):
        SubprocessCodexCliRunner().run(command, timeout_seconds=5)


def test_codex_cli_client_uses_explicit_runner_and_config(tmp_path: Path) -> None:
    runner = FakeCodexCliRunner()
    exec_config = CodexCliExecConfig(executable="codex-test")
    auth_config = CodexCliAuthConfig()

    client = make_client(runner, tmp_path, exec_config=exec_config, auth_config=auth_config)

    assert client.runner is runner
    assert client.exec_config is exec_config
    assert client.auth_config is auth_config


def test_codex_cli_client_requires_explicit_working_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="working_directory must be a path"):
        CodexCliClient(
            runner=FakeCodexCliRunner(),
            exec_config=CodexCliExecConfig(),
            auth_config=CodexCliAuthConfig(),
            working_directory=cast(Path, None),
            output_schema_dir=tmp_path,
        )
