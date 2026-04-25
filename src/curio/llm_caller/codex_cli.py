import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from curio.llm_caller.models import (
    JsonValue,
    LlmInvalidOutputError,
    LlmMessage,
    LlmMessageRole,
    LlmRequest,
    LlmResponse,
    ProviderName,
)
from curio.llm_caller.providers import (
    ProviderCallTiming,
    build_json_llm_response,
    build_provider_usage,
)

CODEX_CLI_DEFAULT_EXECUTABLE = "codex"
CODEX_CLI_DEFAULT_SANDBOX = "read-only"
CODEX_CLI_DEFAULT_COLOR = "never"
CODEX_CLI_AGENT_MESSAGE_TYPES = frozenset(("agent_message", "assistant_message"))


@dataclass(frozen=True, slots=True)
class CodexCliExecConfig:
    executable: str = CODEX_CLI_DEFAULT_EXECUTABLE
    sandbox: str = CODEX_CLI_DEFAULT_SANDBOX
    color: str = CODEX_CLI_DEFAULT_COLOR
    ephemeral: bool = True
    json_events: bool = True
    skip_git_repo_check: bool = False
    ignore_user_config: bool = False
    extra_config: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_config_string(self.executable, "executable")
        _require_config_string(self.sandbox, "sandbox")
        _require_config_string(self.color, "color")
        for override in self.extra_config:
            _require_config_string(override, "config override")
        object.__setattr__(self, "extra_config", tuple(self.extra_config))


@dataclass(frozen=True, slots=True)
class CodexCliCommand:
    argv: tuple[str, ...]
    stdin_text: str


@dataclass(frozen=True, slots=True)
class CodexCliExecResult:
    output_value: JsonValue
    usage_input_tokens: float | int | None
    usage_cached_input_tokens: float | int | None
    usage_output_tokens: float | int | None
    usage_reasoning_tokens: float | int | None
    usage_total_tokens: float | int | None
    warnings: tuple[str, ...] = ()


def build_codex_exec_command(
    request: LlmRequest,
    *,
    output_schema_path: Path,
    config: CodexCliExecConfig | None = None,
    working_directory: Path | None = None,
) -> CodexCliCommand:
    exec_config = CodexCliExecConfig() if config is None else config
    argv = [exec_config.executable, "exec"]
    if exec_config.json_events:
        argv.append("--json")
    if exec_config.ephemeral:
        argv.append("--ephemeral")
    if exec_config.skip_git_repo_check:
        argv.append("--skip-git-repo-check")
    if exec_config.ignore_user_config:
        argv.append("--ignore-user-config")
    argv.extend(["--sandbox", exec_config.sandbox])
    argv.extend(["--color", exec_config.color])
    argv.extend(["--output-schema", str(output_schema_path)])
    if working_directory is not None:
        argv.extend(["--cd", str(working_directory)])
    for override in exec_config.extra_config:
        argv.extend(["--config", override])
    if request.model is not None:
        argv.extend(["--model", request.model])
    argv.append("-")
    return CodexCliCommand(argv=tuple(argv), stdin_text=build_codex_exec_prompt(request))


def build_codex_exec_prompt(request: LlmRequest) -> str:
    return "\n\n".join(
        (
            "Curio LLM request",
            f"Request ID: {request.request_id}",
            f"Workflow: {request.workflow}",
            "Instructions:\n" + request.instructions,
            "Input messages:\n" + "\n\n".join(_format_message(message) for message in request.input),
            "Return only the final JSON value that matches the provided --output-schema.",
        )
    )


def parse_codex_exec_jsonl(stdout: str) -> CodexCliExecResult:
    final_message: str | None = None
    usage_payload: Mapping[str, JsonValue] | None = None
    warnings: list[str] = []

    for event in _iter_jsonl_events(stdout):
        event_type = _optional_string(event.get("type"))
        if event_type is None:
            raise LlmInvalidOutputError("codex_cli JSONL event is missing type")

        if event_type == "item.completed":
            item = _optional_mapping(event.get("item"))
            if item is None:
                raise LlmInvalidOutputError("codex_cli item.completed event is missing item")
            item_type = _optional_string(item.get("type")) or _optional_string(item.get("item_type"))
            if item_type in CODEX_CLI_AGENT_MESSAGE_TYPES:
                final_message = _extract_agent_message_text(item)
            elif item_type == "error":
                warnings.append(_extract_error_message(item))
        elif event_type in CODEX_CLI_AGENT_MESSAGE_TYPES:
            final_message = _extract_agent_message_text(event)
        elif event_type == "task_complete":
            final_message = _require_string(event.get("last_agent_message"), "last_agent_message")
        elif event_type == "turn.completed":
            usage_payload = _optional_mapping(event.get("usage"))
        elif event_type == "token_count" and usage_payload is None:
            usage_payload = _usage_from_token_count(event)

    if final_message is None:
        raise LlmInvalidOutputError("codex_cli JSONL did not include a final agent message")

    output_value = _parse_final_json(final_message)
    total_tokens = _optional_non_negative_number(_usage_field(usage_payload, "total_tokens"), "total_tokens")
    return CodexCliExecResult(
        output_value=output_value,
        usage_input_tokens=_optional_non_negative_number(_usage_field(usage_payload, "input_tokens"), "input_tokens"),
        usage_cached_input_tokens=_optional_non_negative_number(
            _usage_field(usage_payload, "cached_input_tokens"),
            "cached_input_tokens",
        ),
        usage_output_tokens=_optional_non_negative_number(_usage_field(usage_payload, "output_tokens"), "output_tokens"),
        usage_reasoning_tokens=_optional_non_negative_number(
            _usage_field(usage_payload, "reasoning_output_tokens", "reasoning_tokens"),
            "reasoning_tokens",
        ),
        usage_total_tokens=total_tokens if total_tokens is not None else _computed_total_tokens(usage_payload),
        warnings=tuple(warnings),
    )


def build_codex_llm_response(
    request: LlmRequest,
    result: CodexCliExecResult,
    timing: ProviderCallTiming,
    *,
    model: str | None = None,
) -> LlmResponse:
    usage = build_provider_usage(
        timing,
        input_tokens=result.usage_input_tokens,
        cached_input_tokens=result.usage_cached_input_tokens,
        output_tokens=result.usage_output_tokens,
        reasoning_tokens=result.usage_reasoning_tokens,
        total_tokens=result.usage_total_tokens,
        metered_objects=(),
        thinking_seconds=None,
    )
    return build_json_llm_response(
        request,
        provider=ProviderName.CODEX_CLI,
        model=model,
        output_value=result.output_value,
        usage=usage,
        warnings=result.warnings,
    )


def _format_message(message: LlmMessage) -> str:
    role = cast(LlmMessageRole, message.role)
    return "\n".join(
        (
            f"<message role={role.value}>",
            "\n".join(part.text for part in message.content),
            "</message>",
        )
    )


def _iter_jsonl_events(stdout: str) -> list[Mapping[str, JsonValue]]:
    events: list[Mapping[str, JsonValue]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LlmInvalidOutputError(f"codex_cli JSONL line {line_number} is not valid JSON") from exc
        if not isinstance(event, Mapping):
            raise LlmInvalidOutputError(f"codex_cli JSONL line {line_number} must be an object")
        events.append(cast(Mapping[str, JsonValue], event))
    return events


def _extract_agent_message_text(payload: Mapping[str, JsonValue]) -> str:
    text = payload.get("text")
    if text is None:
        text = payload.get("message")
    return _require_string(text, "agent message")


def _extract_error_message(payload: Mapping[str, JsonValue]) -> str:
    message = payload.get("message")
    if message is None:
        return "codex_cli emitted an error item"
    return _require_string(message, "error message")


def _parse_final_json(final_message: str) -> JsonValue:
    try:
        return json.loads(final_message)
    except json.JSONDecodeError as exc:
        raise LlmInvalidOutputError("codex_cli final agent message is not valid JSON") from exc


def _usage_from_token_count(event: Mapping[str, JsonValue]) -> Mapping[str, JsonValue] | None:
    info = _optional_mapping(event.get("info"))
    if info is None:
        return None
    return _optional_mapping(info.get("last_token_usage")) or _optional_mapping(info.get("total_token_usage"))


def _usage_field(usage_payload: Mapping[str, JsonValue] | None, *names: str) -> object:
    if usage_payload is None:
        return None
    for name in names:
        value = usage_payload.get(name)
        if value is not None:
            return value
    return None


def _computed_total_tokens(usage_payload: Mapping[str, JsonValue] | None) -> float | int | None:
    input_tokens = _optional_non_negative_number(_usage_field(usage_payload, "input_tokens"), "input_tokens")
    output_tokens = _optional_non_negative_number(_usage_field(usage_payload, "output_tokens"), "output_tokens")
    if input_tokens is None or output_tokens is None:
        return None
    return input_tokens + output_tokens


def _optional_mapping(value: object) -> Mapping[str, JsonValue] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise LlmInvalidOutputError("codex_cli JSONL field must be an object")
    return cast(Mapping[str, JsonValue], value)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return _require_string(value, "string field")


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise LlmInvalidOutputError(f"{field_name} must be a string")
    if not value.strip():
        raise LlmInvalidOutputError(f"{field_name} must not be empty")
    return value


def _require_config_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _optional_non_negative_number(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise LlmInvalidOutputError(f"{field_name} must be a non-negative number")
    if value < 0:
        raise LlmInvalidOutputError(f"{field_name} must be a non-negative number")
    return value
