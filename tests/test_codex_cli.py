import json
from pathlib import Path
from typing import cast

import pytest

from curio.llm_caller import (
    CodexCliExecConfig,
    JsonSchemaOutput,
    LlmInvalidOutputError,
    LlmMessage,
    LlmMessageRole,
    LlmRequest,
    ProviderCallTiming,
    ProviderName,
    TextContentPart,
    build_codex_exec_command,
    build_codex_exec_prompt,
    build_codex_llm_response,
    parse_codex_exec_jsonl,
)


def make_request(model: str | None = "gpt-test") -> LlmRequest:
    return LlmRequest(
        request_id="translate-test",
        workflow="translate",
        model=model,
        instructions="Return translated blocks as JSON.",
        input=[
            LlmMessage(role="system", content=[TextContentPart(text="System context.")]),
            LlmMessage(role="user", content=[TextContentPart(text="Bonjour."), TextContentPart(text="Salut.")]),
        ],
        output=JsonSchemaOutput(name="curio_translation_model_output", schema={"type": "object"}),
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
        "-",
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
