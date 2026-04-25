import json
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Protocol, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError

from curio.llm_caller.auth import CodexCliAuthConfig, CodexCliAuthMode
from curio.llm_caller.models import (
    JsonValue,
    LlmCapability,
    LlmConfigurationError,
    LlmInvalidOutputError,
    LlmMessage,
    LlmMessageRole,
    LlmProviderNotFoundError,
    LlmRejectedRequestError,
    LlmRequest,
    LlmResponse,
    LlmSchemaValidationError,
    LlmTimeoutError,
    ProviderName,
)
from curio.llm_caller.providers import (
    ProviderCallTiming,
    ProviderClientBase,
    ProviderClientConfig,
    build_json_llm_response,
    build_provider_usage,
    measure_provider_call,
)

CODEX_CLI_DEFAULT_EXECUTABLE = "codex"
CODEX_CLI_DEFAULT_SANDBOX = "read-only"
CODEX_CLI_DEFAULT_COLOR = "never"
CODEX_CLI_AGENT_MESSAGE_TYPES = frozenset(("agent_message", "assistant_message"))
CODEX_CLI_CAPABILITIES = (
    LlmCapability.TEXT_GENERATION,
    LlmCapability.JSON_SCHEMA_OUTPUT,
    LlmCapability.TOKEN_USAGE,
    LlmCapability.CACHED_INPUT_USAGE,
    LlmCapability.REASONING_TOKEN_USAGE,
    LlmCapability.SUBPROCESS,
)


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


@dataclass(frozen=True, slots=True)
class CodexCliRunResult:
    stdout: str
    stderr: str
    return_code: int
    timing: ProviderCallTiming

    def __post_init__(self) -> None:
        _require_string_type(self.stdout, "stdout")
        _require_string_type(self.stderr, "stderr")
        if not isinstance(self.return_code, int) or isinstance(self.return_code, bool):
            raise ValueError("return_code must be an integer")


class CodexCliRunner(Protocol):
    def run(self, command: CodexCliCommand, timeout_seconds: int) -> CodexCliRunResult: ...


class SubprocessCodexCliRunner:
    def run(self, command: CodexCliCommand, timeout_seconds: int) -> CodexCliRunResult:
        try:
            completed, timing = measure_provider_call(
                lambda: subprocess.run(
                    command.argv,
                    input=command.stdin_text,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            )
        except FileNotFoundError as exc:
            raise LlmProviderNotFoundError("codex_cli executable not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise LlmTimeoutError("codex_cli subprocess timed out") from exc
        return CodexCliRunResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            return_code=completed.returncode,
            timing=timing,
        )


class CodexCliClient(ProviderClientBase):
    def __init__(
        self,
        *,
        runner: CodexCliRunner | None = None,
        exec_config: CodexCliExecConfig | None = None,
        auth_config: CodexCliAuthConfig | None = None,
        working_directory: Path | None = None,
        output_schema_dir: Path | None = None,
        default_model: str | None = None,
    ) -> None:
        super().__init__(
            ProviderClientConfig(
                provider=ProviderName.CODEX_CLI,
                capabilities=CODEX_CLI_CAPABILITIES,
                default_model=default_model,
            )
        )
        self.runner = SubprocessCodexCliRunner() if runner is None else runner
        self.exec_config = CodexCliExecConfig() if exec_config is None else exec_config
        self.auth_config = CodexCliAuthConfig() if auth_config is None else auth_config
        self.working_directory = working_directory
        self.output_schema_dir = output_schema_dir

    def complete_after_capability_check(self, request: LlmRequest) -> LlmResponse:
        _validate_codex_auth_config(self.auth_config)
        effective_request = _request_with_default_model(request, self.config.default_model)
        schema_parent = None if self.output_schema_dir is None else str(self.output_schema_dir)
        with tempfile.TemporaryDirectory(dir=schema_parent) as schema_dir:
            output_schema_path = Path(schema_dir) / "output.schema.json"
            _write_output_schema(effective_request, output_schema_path)
            command = build_codex_exec_command(
                effective_request,
                output_schema_path=output_schema_path,
                config=self.exec_config,
                working_directory=self.working_directory,
            )
            run_result = self._run(command, timeout_seconds=effective_request.timeout_seconds)
        if run_result.return_code != 0:
            raise LlmRejectedRequestError(f"codex_cli subprocess exited with status {run_result.return_code}")
        exec_result = parse_codex_exec_jsonl(run_result.stdout)
        _validate_output_schema(effective_request, exec_result.output_value)
        return build_codex_llm_response(
            effective_request,
            exec_result,
            run_result.timing,
            model=effective_request.model,
        )

    def _run(self, command: CodexCliCommand, *, timeout_seconds: int) -> CodexCliRunResult:
        try:
            return self.runner.run(command, timeout_seconds)
        except FileNotFoundError as exc:
            raise LlmProviderNotFoundError("codex_cli executable not found") from exc
        except (TimeoutError, subprocess.TimeoutExpired) as exc:
            raise LlmTimeoutError("codex_cli subprocess timed out") from exc


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


def _validate_codex_auth_config(auth_config: CodexCliAuthConfig) -> None:
    mode = cast(CodexCliAuthMode, auth_config.mode)
    if mode == CodexCliAuthMode.API_KEY:
        raise LlmConfigurationError("codex_cli API-key handoff is not implemented")


def _request_with_default_model(request: LlmRequest, default_model: str | None) -> LlmRequest:
    if request.model is not None or default_model is None:
        return request
    return replace(request, model=default_model)


def _write_output_schema(request: LlmRequest, output_schema_path: Path) -> None:
    output_schema_path.write_text(json.dumps(request.output.schema), encoding="utf-8")


def _validate_output_schema(request: LlmRequest, output_value: JsonValue) -> None:
    validator = Draft202012Validator(dict(request.output.schema), format_checker=FormatChecker())
    try:
        validator.validate(output_value)
    except JsonSchemaLibraryError as exc:
        raise LlmSchemaValidationError("codex_cli output did not match requested schema") from exc


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


def _require_string_type(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _optional_non_negative_number(value: object, field_name: str) -> float | int | None:
    if value is None:
        return None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise LlmInvalidOutputError(f"{field_name} must be a non-negative number")
    if value < 0:
        raise LlmInvalidOutputError(f"{field_name} must be a non-negative number")
    return value
