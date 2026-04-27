import json
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError

from curio.llm_caller.auth import CodexCliAuthConfig, CodexCliAuthMode
from curio.llm_caller.local_files import (
    local_file_content_parts,
    validate_local_file_content_part,
)
from curio.llm_caller.models import (
    JsonObject,
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
    LocalFileContentPart,
    ProviderName,
    TextContentPart,
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
    LlmCapability.FILE_INPUT,
    LlmCapability.IMAGE_INPUT,
    LlmCapability.PDF_INPUT,
    LlmCapability.OCR,
    LlmCapability.MARKDOWN_OUTPUT,
    LlmCapability.PLAIN_TEXT_OUTPUT,
    LlmCapability.SUGGESTED_FILE_OUTPUT,
    LlmCapability.MULTIPLE_FILE_OUTPUT,
    LlmCapability.RELATIVE_PATH_OUTPUT,
)


class CodexCliReasoningEffort(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class CodexCliVerbosity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class CodexCliExecConfig:
    executable: str = CODEX_CLI_DEFAULT_EXECUTABLE
    sandbox: str = CODEX_CLI_DEFAULT_SANDBOX
    color: str = CODEX_CLI_DEFAULT_COLOR
    ephemeral: bool = True
    json_events: bool = True
    skip_git_repo_check: bool = False
    ignore_user_config: bool = False
    model_reasoning_effort: CodexCliReasoningEffort | str | None = None
    model_verbosity: CodexCliVerbosity | str | None = None
    extra_config: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_config_string(self.executable, "executable")
        _require_config_string(self.sandbox, "sandbox")
        _require_config_string(self.color, "color")
        object.__setattr__(
            self,
            "model_reasoning_effort",
            _coerce_optional_str_enum(
                self.model_reasoning_effort,
                "model_reasoning_effort",
                CodexCliReasoningEffort,
            ),
        )
        object.__setattr__(
            self,
            "model_verbosity",
            _coerce_optional_str_enum(self.model_verbosity, "model_verbosity", CodexCliVerbosity),
        )
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
        runner: CodexCliRunner,
        exec_config: CodexCliExecConfig,
        auth_config: CodexCliAuthConfig,
        working_directory: Path,
        model: str,
        timeout_seconds: int,
        output_schema_dir: Path | None = None,
    ) -> None:
        super().__init__(
            ProviderClientConfig(
                provider=ProviderName.CODEX_CLI,
                capabilities=CODEX_CLI_CAPABILITIES,
            )
        )
        self.runner = runner
        self.exec_config = exec_config
        self.auth_config = auth_config
        if not isinstance(working_directory, Path):
            raise ValueError("working_directory must be a path")
        self.working_directory = working_directory
        self.model = _require_config_string(model, "model")
        self.timeout_seconds = _require_positive_int(timeout_seconds, "timeout_seconds")
        self.output_schema_dir = output_schema_dir

    def complete_after_capability_check(self, request: LlmRequest) -> LlmResponse:
        _validate_codex_auth_config(self.auth_config)
        schema_parent = None if self.output_schema_dir is None else str(self.output_schema_dir)
        with tempfile.TemporaryDirectory(dir=schema_parent) as schema_dir:
            output_schema_path = Path(schema_dir) / "output.schema.json"
            _write_output_schema(request, output_schema_path)
            command = build_codex_exec_command(
                request,
                model=self.model,
                output_schema_path=output_schema_path,
                config=self.exec_config,
                working_directory=self.working_directory,
            )
            run_result = self._run(command, timeout_seconds=self.timeout_seconds)
        if run_result.return_code != 0:
            raise LlmRejectedRequestError(_codex_exit_status_message(run_result))
        exec_result = parse_codex_exec_jsonl(run_result.stdout)
        _validate_output_schema(request, exec_result.output_value)
        return build_codex_llm_response(
            request,
            exec_result,
            run_result.timing,
            model=self.model,
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
    model: str,
    output_schema_path: Path,
    config: CodexCliExecConfig,
    working_directory: Path,
) -> CodexCliCommand:
    if not isinstance(working_directory, Path):
        raise ValueError("working_directory must be a path")
    _require_config_string(model, "model")
    argv = [config.executable, "exec"]
    if config.json_events:
        argv.append("--json")
    if config.ephemeral:
        argv.append("--ephemeral")
    if config.skip_git_repo_check:
        argv.append("--skip-git-repo-check")
    if config.ignore_user_config:
        argv.append("--ignore-user-config")
    argv.extend(["--sandbox", config.sandbox])
    argv.extend(["--color", config.color])
    argv.extend(["--output-schema", str(output_schema_path)])
    argv.extend(["--cd", str(working_directory)])
    if config.model_reasoning_effort is not None:
        model_reasoning_effort = cast(CodexCliReasoningEffort, config.model_reasoning_effort)
        argv.extend(["--config", f'model_reasoning_effort="{model_reasoning_effort.value}"'])
    if config.model_verbosity is not None:
        model_verbosity = cast(CodexCliVerbosity, config.model_verbosity)
        argv.extend(["--config", f'model_verbosity="{model_verbosity.value}"'])
    for override in config.extra_config:
        argv.extend(["--config", override])
    for local_file in local_file_content_parts(request):
        validate_local_file_content_part(
            local_file,
            provider_name="codex_cli",
            allowed_root=working_directory,
            allowed_root_description="configured working directory",
        )
        if _is_codex_image(local_file):
            argv.extend(["--image", local_file.path])
    argv.extend(["--model", model])
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


def _write_output_schema(request: LlmRequest, output_schema_path: Path) -> None:
    output_schema_path.write_text(json.dumps(_codex_response_format_schema(request.output.schema)), encoding="utf-8")


def _codex_response_format_schema(schema: Mapping[str, JsonValue]) -> JsonValue:
    return _without_unsupported_codex_schema_keywords(schema)


def _without_unsupported_codex_schema_keywords(value: JsonValue) -> JsonValue:
    if isinstance(value, Mapping):
        sanitized: JsonObject = {}
        for key, child in value.items():
            if key in ("uniqueItems", "allOf", "if", "then", "else"):
                continue
            if key == "const":
                sanitized["enum"] = [_without_unsupported_codex_schema_keywords(child)]
            elif key == "oneOf":
                type_union = _simple_one_of_type_union(child)
                if type_union is not None:
                    sanitized.update(type_union)
            else:
                sanitized[key] = _without_unsupported_codex_schema_keywords(child)
        return sanitized
    if isinstance(value, list):
        return [_without_unsupported_codex_schema_keywords(item) for item in value]
    return value


def _simple_one_of_type_union(value: JsonValue) -> JsonObject | None:
    if not isinstance(value, list):
        return None
    types: list[str] = []
    merged_constraints: JsonObject = {}
    for option in value:
        if not isinstance(option, Mapping):
            return None
        schema_type = option.get("type")
        if not isinstance(schema_type, str):
            return None
        types.append(schema_type)
        if schema_type == "null":
            continue
        for key, child in option.items():
            if key != "type":
                merged_constraints[key] = _without_unsupported_codex_schema_keywords(child)
    return {"type": types, **merged_constraints}


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
            "\n".join(_format_content_part(part) for part in message.content),
            "</message>",
        )
    )


def _format_content_part(part: TextContentPart | LocalFileContentPart) -> str:
    if isinstance(part, TextContentPart):
        return part.text
    return "\n".join(
        (
            "<local_file>",
            f"name: {part.name or ''}",
            f"path: {part.path}",
            f"mime_type: {part.mime_type}",
            f"sha256: {part.sha256}",
            "</local_file>",
        )
    )


def _is_codex_image(part: LocalFileContentPart) -> bool:
    return part.mime_type.casefold().startswith("image/")


def _iter_jsonl_events(stdout: str) -> list[Mapping[str, JsonValue]]:
    events: list[Mapping[str, JsonValue]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        stripped_line = line.strip()
        if not stripped_line or _is_codex_stdout_diagnostic(stripped_line):
            continue
        try:
            event = json.loads(stripped_line)
        except json.JSONDecodeError as exc:
            raise LlmInvalidOutputError(f"codex_cli JSONL line {line_number} is not valid JSON") from exc
        if not isinstance(event, Mapping):
            raise LlmInvalidOutputError(f"codex_cli JSONL line {line_number} must be an object")
        events.append(cast(Mapping[str, JsonValue], event))
    return events


def _codex_exit_status_message(run_result: CodexCliRunResult) -> str:
    message = f"codex_cli subprocess exited with status {run_result.return_code}"
    detail = _codex_failure_detail(run_result.stdout)
    if detail is None:
        return message
    return f"{message}: {detail}"


def _codex_failure_detail(stdout: str) -> str | None:
    messages: list[str] = []
    for line in stdout.splitlines():
        stripped_line = line.strip()
        if not stripped_line or _is_codex_stdout_diagnostic(stripped_line):
            continue
        try:
            event = json.loads(stripped_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        event_type_value = event.get("type")
        if not isinstance(event_type_value, str):
            continue
        event_type = event_type_value
        if event_type == "error":
            message = event.get("message")
            if isinstance(message, str) and message.strip():
                messages.append(message)
        elif event_type == "turn.failed":
            error = event.get("error")
            if isinstance(error, Mapping):
                message = error.get("message")
                if isinstance(message, str) and message.strip():
                    messages.append(message)
    if not messages:
        return None
    return messages[-1]


def _is_codex_stdout_diagnostic(line: str) -> bool:
    return line == "Reading additional input from stdin..." or _is_codex_log_line(line)


def _is_codex_log_line(line: str) -> bool:
    if len(line) < 31 or line[4:5] != "-" or line[7:8] != "-" or line[10:11] != "T":
        return False
    return " WARN " in line or " INFO " in line or " DEBUG " in line or " TRACE " in line or " ERROR " in line


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


def _coerce_optional_str_enum[StrEnumT: StrEnum](
    value: object,
    field_name: str,
    enum_type: type[StrEnumT],
) -> StrEnumT | None:
    if value is None:
        return None
    if isinstance(value, enum_type):
        return value
    value = _require_config_string(value, field_name)
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed_values = ", ".join(member.value for member in enum_type)
        raise ValueError(f"{field_name} must be one of: {allowed_values}") from exc


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
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
