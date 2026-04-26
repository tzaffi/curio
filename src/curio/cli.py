import json
import uuid
from pathlib import Path
from typing import Annotated, NoReturn, cast

import click
import typer

from curio.config import ConfigError, CurioConfig, load_config
from curio.llm_caller import (
    KeyringSecretStore,
    LlmCallerError,
    LlmClient,
    SdkOpenAiApiTransport,
    SubprocessCodexCliRunner,
    build_llm_caller_client,
)
from curio.schemas import SchemaValidationError
from curio.translate import (
    DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD,
    DEFAULT_TARGET_LANGUAGE,
    Block,
    TranslationError,
    TranslationRequest,
    TranslationResponse,
    TranslationService,
)

app = typer.Typer(
    help="Semantic labeling of iMsgX artifacts in preparation for a knowledgebase.",
    invoke_without_command=True,
)

RAW_CLI_BLOCK_ID = 1
RAW_CLI_BLOCK_NAME = "cli_text"
LLM_CALLER_REQUIRED_MESSAGE = "llm_caller must be configured with --llm-caller, input JSON, or translate.llm_caller"


@app.callback()
def main(ctx: typer.Context) -> None:
    """Curio CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _reserved(command: str) -> None:
    typer.echo(f"{command} is reserved but not implemented yet.", err=True)
    raise typer.Exit(1)


def _build_llm_caller_client(
    llm_caller: str,
    config_path: Path | None,
    config: CurioConfig | None = None,
) -> LlmClient:
    curio_config = load_config(config_path) if config is None else config
    return build_llm_caller_client(
        llm_caller,
        curio_config,
        secret_store=KeyringSecretStore(),
        codex_runner=SubprocessCodexCliRunner(),
        openai_transport=SdkOpenAiApiTransport(),
        codex_working_directory=Path.cwd(),
    )


def _build_translation_service(
    llm_caller: str,
    config_path: Path | None,
    config: CurioConfig | None = None,
) -> TranslationService:
    if config is None:
        return TranslationService(llm_client=_build_llm_caller_client(llm_caller, config_path))
    return TranslationService(llm_client=_build_llm_caller_client(llm_caller, config_path, config=config))


def _fail_usage(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(2)


def _fail_runtime(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


def _parameter_was_set(ctx: typer.Context, name: str) -> bool:
    return ctx.get_parameter_source(name) == click.core.ParameterSource.COMMANDLINE


def _read_stdin_text() -> str | None:
    stdin = click.get_text_stream("stdin")
    if stdin.isatty():
        return None
    text = stdin.read()
    return text if text else None


def _read_text_file(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        _fail_usage(f"could not read {label}: {exc}")


def _load_translation_request(path: Path) -> TranslationRequest:
    raw_json = _read_text_file(path, "--input-json")
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        _fail_usage(f"--input-json must contain valid JSON: {exc.msg}")
    return TranslationRequest.from_json(payload)


def _new_translation_request_id() -> str:
    return f"translate-{uuid.uuid4().hex}"


def _raw_translation_request(
    raw_text: str,
    *,
    source_language: str | None,
    target_language: str,
    english_confidence_threshold: float,
    llm_caller: str | None,
) -> TranslationRequest:
    return TranslationRequest(
        request_id=_new_translation_request_id(),
        target_language=target_language,
        english_confidence_threshold=english_confidence_threshold,
        blocks=[
            Block(
                block_id=RAW_CLI_BLOCK_ID,
                name=RAW_CLI_BLOCK_NAME,
                source_language_hint=source_language,
                text=raw_text,
            )
        ],
        llm_caller=llm_caller,
    )


def _apply_structured_request_overrides(
    ctx: typer.Context,
    request: TranslationRequest,
    *,
    target_language: str,
    english_confidence_threshold: float,
    llm_caller: str | None,
) -> TranslationRequest:
    selected_llm_caller = llm_caller if _parameter_was_set(ctx, "llm_caller") else request.llm_caller
    return TranslationRequest(
        request_id=request.request_id,
        target_language=target_language if _parameter_was_set(ctx, "target_language") else request.target_language,
        english_confidence_threshold=english_confidence_threshold
        if _parameter_was_set(ctx, "english_confidence_threshold")
        else request.english_confidence_threshold,
        blocks=request.blocks,
        llm_caller=selected_llm_caller,
    )


def _translation_request_from_cli(
    ctx: typer.Context,
    *,
    text: str | None,
    input_file: Path | None,
    input_json: Path | None,
    source_language: str | None,
    target_language: str,
    english_confidence_threshold: float,
    llm_caller: str | None,
) -> TranslationRequest:
    stdin_text = _read_stdin_text()
    input_mode_count = sum(
        (
            text is not None,
            input_file is not None,
            input_json is not None,
            stdin_text is not None,
        )
    )
    if input_mode_count != 1:
        _fail_usage("exactly one input mode must be provided")

    try:
        if input_json is not None:
            if source_language is not None:
                _fail_usage("--source-language can only be used with raw text input")
            return _apply_structured_request_overrides(
                ctx,
                _load_translation_request(input_json),
                target_language=target_language,
                english_confidence_threshold=english_confidence_threshold,
                llm_caller=llm_caller,
            )

        if text is not None:
            raw_text = text
        elif input_file is not None:
            raw_text = _read_text_file(input_file, "--input-file")
        else:
            raw_text = cast(str, stdin_text)
        return _raw_translation_request(
            raw_text,
            source_language=source_language,
            target_language=target_language,
            english_confidence_threshold=english_confidence_threshold,
            llm_caller=llm_caller,
        )
    except (SchemaValidationError, TranslationError, ValueError) as exc:
        _fail_usage(str(exc))


def _render_translation_output(
    request: TranslationRequest,
    response: TranslationResponse,
    *,
    structured_output: bool,
) -> str:
    if structured_output:
        return json.dumps(response.to_json(), ensure_ascii=False) + "\n"

    block = response.blocks[0]
    text = block.translated_text if block.translation_required else request.blocks[0].text
    return cast(str, text) + "\n"


def _emit_warnings(response: TranslationResponse) -> None:
    for warning in response.warnings:
        typer.echo(warning, err=True)
    for block in response.blocks:
        for warning in block.warnings:
            typer.echo(warning, err=True)


def _write_output(rendered_output: str, output: Path | None) -> None:
    if output is None:
        typer.echo(rendered_output, nl=False)
        return
    try:
        output.write_text(rendered_output, encoding="utf-8")
    except OSError as exc:
        _fail_runtime(f"could not write --output: {exc}")


def _request_llm_caller(request: TranslationRequest) -> str:
    if request.llm_caller is None:
        _fail_usage(LLM_CALLER_REQUIRED_MESSAGE)
    return request.llm_caller


def _request_with_llm_caller(request: TranslationRequest, llm_caller: str) -> TranslationRequest:
    return TranslationRequest(
        request_id=request.request_id,
        target_language=request.target_language,
        english_confidence_threshold=request.english_confidence_threshold,
        blocks=request.blocks,
        llm_caller=llm_caller,
    )


def _resolve_translation_request_llm_caller(
    request: TranslationRequest,
    config_path: Path | None,
) -> tuple[TranslationRequest, CurioConfig | None]:
    if request.llm_caller is not None:
        return request, None
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        _fail_runtime(str(exc))
    if config.translate_config.llm_caller is None:
        _fail_usage(LLM_CALLER_REQUIRED_MESSAGE)
    return _request_with_llm_caller(request, config.translate_config.llm_caller), config


@app.command("translate")
def translate(
    ctx: typer.Context,
    text: Annotated[str | None, typer.Argument(help="Raw text to translate.")] = None,
    input_file: Annotated[Path | None, typer.Option("--input-file", help="Read raw text from a UTF-8 file.")] = None,
    input_json: Annotated[
        Path | None,
        typer.Option("--input-json", help="Read a structured translation request JSON file."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print the full translation response JSON.")] = False,
    output: Annotated[Path | None, typer.Option("--output", help="Write output to a UTF-8 file.")] = None,
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Read Curio runtime config JSON. Defaults to ./config.json."),
    ] = None,
    source_language: Annotated[
        str | None,
        typer.Option("--source-language", help="Optional source-language hint for raw text."),
    ] = None,
    target_language: Annotated[
        str,
        typer.Option("--target-language", help="Target language. V1 accepts only en."),
    ] = DEFAULT_TARGET_LANGUAGE,
    english_confidence_threshold: Annotated[
        float,
        typer.Option("--english-confidence-threshold", help="Confidence threshold for treating text as English."),
    ] = DEFAULT_ENGLISH_CONFIDENCE_THRESHOLD,
    llm_caller: Annotated[
        str | None,
        typer.Option("--llm-caller", help="Override the configured or input JSON named LLM caller."),
    ] = None,
) -> None:
    """Translate text into English."""
    request = _translation_request_from_cli(
        ctx,
        text=text,
        input_file=input_file,
        input_json=input_json,
        source_language=source_language,
        target_language=target_language,
        english_confidence_threshold=english_confidence_threshold,
        llm_caller=llm_caller,
    )
    request, config = _resolve_translation_request_llm_caller(request, config_path)
    try:
        if config is None:
            response = _build_translation_service(_request_llm_caller(request), config_path).translate(request)
        else:
            response = _build_translation_service(_request_llm_caller(request), config_path, config=config).translate(
                request
            )
    except (ConfigError, LlmCallerError, TranslationError) as exc:
        _fail_runtime(str(exc))

    structured_output = json_output or input_json is not None
    if not structured_output:
        _emit_warnings(response)
    _write_output(
        _render_translation_output(request, response, structured_output=structured_output),
        output,
    )


@app.command("curate")
def curate() -> None:
    """Run the main Curio curation workflow."""
    _reserved("curate")


@app.command("bootstrap")
def bootstrap() -> None:
    """Bootstrap the label registry."""
    _reserved("bootstrap")


@app.command("schema")
def schema() -> None:
    """Validate or inspect Curio schemas."""
    _reserved("schema")


@app.command("doctor")
def doctor() -> None:
    """Diagnose local Curio configuration and provider prerequisites."""
    _reserved("doctor")
