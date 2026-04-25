import json
import uuid
from pathlib import Path
from typing import Annotated, NoReturn, cast

import click
import typer

from curio.llm_caller import (
    LlmCallerError,
    LlmProviderNotFoundError,
    LlmRequest,
    LlmResponse,
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
DEFAULT_PROVIDER = "codex_cli"
DEFAULT_TIMEOUT_SECONDS = 300


@app.callback()
def main(ctx: typer.Context) -> None:
    """Curio CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _reserved(command: str) -> None:
    typer.echo(f"{command} is reserved but not implemented yet.", err=True)
    raise typer.Exit(1)


class _ProviderClientNotImplemented:
    def complete(self, request: LlmRequest) -> LlmResponse:
        provider = request.metadata.get("provider") or DEFAULT_PROVIDER
        raise LlmProviderNotFoundError(f"provider client is not implemented yet: {provider}")


def _build_translation_service() -> TranslationService:
    return TranslationService(llm_client=_ProviderClientNotImplemented())


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
    provider: str,
    model: str | None,
    timeout_seconds: int,
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
        provider=provider,
        model=model,
        timeout_seconds=timeout_seconds,
    )


def _apply_structured_request_overrides(
    ctx: typer.Context,
    request: TranslationRequest,
    *,
    target_language: str,
    english_confidence_threshold: float,
    provider: str,
    model: str | None,
    timeout_seconds: int,
) -> TranslationRequest:
    return TranslationRequest(
        request_id=request.request_id,
        target_language=target_language if _parameter_was_set(ctx, "target_language") else request.target_language,
        english_confidence_threshold=english_confidence_threshold
        if _parameter_was_set(ctx, "english_confidence_threshold")
        else request.english_confidence_threshold,
        blocks=request.blocks,
        provider=provider if _parameter_was_set(ctx, "provider") or request.provider is None else request.provider,
        model=model if _parameter_was_set(ctx, "model") or request.model is None else request.model,
        timeout_seconds=timeout_seconds
        if _parameter_was_set(ctx, "timeout_seconds") or request.timeout_seconds is None
        else request.timeout_seconds,
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
    provider: str,
    model: str | None,
    timeout_seconds: int,
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
                provider=provider,
                model=model,
                timeout_seconds=timeout_seconds,
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
            provider=provider,
            model=model,
            timeout_seconds=timeout_seconds,
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
    provider: Annotated[
        str,
        typer.Option("--provider", help="LLM provider override, such as codex_cli or openai_api."),
    ] = DEFAULT_PROVIDER,
    model: Annotated[str | None, typer.Option("--model", help="Provider model override.")] = None,
    timeout_seconds: Annotated[
        int,
        typer.Option("--timeout-seconds", help="Provider-call wall-clock timeout."),
    ] = DEFAULT_TIMEOUT_SECONDS,
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
        provider=provider,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    try:
        response = _build_translation_service().translate(request)
    except (LlmCallerError, TranslationError) as exc:
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
