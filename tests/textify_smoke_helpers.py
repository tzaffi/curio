import json
import math
import shutil
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from curio.config import ConfigError, CurioConfig, LlmCallerConfig, load_config
from curio.llm_caller import (
    LlmClient,
    LlmPricing,
    LlmUsage,
    ProviderName,
    estimate_llm_cost,
)
from curio.llm_caller.codex_cli import CodexCliExecConfig
from curio.textify import (
    TextifyRequest,
    TextifyResponse,
    TextifyService,
    TextifySource,
    file_sha256,
)

JsonObject = dict[str, Any]
MappingPayload = dict[str, Any]
ModelPricing = LlmPricing

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEXTIFY_SMOKE_ROOT = REPO_ROOT / "tmp" / "textify-smoke"
TEXTIFY_SMOKE_FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "textify_smoke"
TEXTIFY_SMOKE_FIXTURE_MANIFEST = TEXTIFY_SMOKE_FIXTURE_ROOT / "manifest.json"
TEXTIFY_SMOKE_CALLERS = (
    "textifier_codex_gpt_54_mini",
    "textifier_codex_gpt_53_codex",
    "textifier_codex_gpt_55",
)


class TextifySmokeHarnessError(RuntimeError):
    pass


def _require_non_empty_string(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class TextifySmokeCase:
    case_id: str
    input_mode: str
    fixture_kind: str
    filename: str
    mime_type: str
    preferred_output_format: str
    expected_output_format: str
    expected_suggested_paths: tuple[str, ...]
    expected_textification_intent: str
    ground_truth_text: str
    preservation_requirements: tuple[str, ...]
    source_language_hint: str | None = None
    model_importance: int = 1
    participates_in_model_ranking: bool = True
    expect_llm_call: bool = True
    expected_status: str = "converted"
    fixture_path: str | None = None
    source_basenames: tuple[str, ...] = ()
    fixture_sha256: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.case_id, "case_id")
        _require_non_empty_string(self.input_mode, "input_mode")
        _require_non_empty_string(self.fixture_kind, "fixture_kind")
        _require_non_empty_string(self.filename, "filename")
        _require_non_empty_string(self.mime_type, "mime_type")
        _require_non_empty_string(self.preferred_output_format, "preferred_output_format")
        _require_non_empty_string(self.expected_output_format, "expected_output_format")
        _require_non_empty_string(self.expected_textification_intent, "expected_textification_intent")
        _require_non_empty_string(self.expected_status, "expected_status")
        if not 1 <= self.model_importance <= 10:
            raise ValueError("model_importance must be between 1 and 10")
        for suggested_path in self.expected_suggested_paths:
            _require_non_empty_string(suggested_path, "expected suggested path")
        for requirement in self.preservation_requirements:
            _require_non_empty_string(requirement, "preservation requirement")
        for basename in self.source_basenames:
            _require_non_empty_string(basename, "source basename")
        if self.fixture_path is not None:
            _require_non_empty_string(self.fixture_path, "fixture_path")
        if self.fixture_sha256 is not None:
            _require_non_empty_string(self.fixture_sha256, "fixture_sha256")


GENERATED_TEXTIFY_SMOKE_CASES = (
    TextifySmokeCase(
        case_id="C-IMG-TXT-01",
        input_mode="artifact_path",
        fixture_kind="png_text",
        filename="plain-note.png",
        mime_type="image/png",
        preferred_output_format="txt",
        expected_output_format="txt",
        expected_suggested_paths=("note.txt",),
        expected_textification_intent="Extract a plain text note without inventing Markdown headings.",
        ground_truth_text="DEPLOY NOTE\nRUN UV SYNC\nTHEN MAKE CHECK\nKEEP README.MD OPEN",
        preservation_requirements=("RUN UV SYNC", "MAKE CHECK", "README.MD"),
    ),
    TextifySmokeCase(
        case_id="C-IMG-CODE-01",
        input_mode="artifact_path",
        fixture_kind="png_code_named",
        filename="foo.py.png",
        mime_type="image/png",
        preferred_output_format="txt",
        expected_output_format="txt",
        expected_suggested_paths=("foo.py",),
        expected_textification_intent="Extract the visible Python file and preserve the visible filename foo.py.",
        ground_truth_text='FILE: foo.py\nDEF GREET(NAME):\n    PRINT("HOLA", NAME)\nGREET("CURIO")',
        preservation_requirements=("foo.py", "DEF GREET(NAME):", 'PRINT("HOLA", NAME)', 'GREET("CURIO")'),
    ),
    TextifySmokeCase(
        case_id="C-IMG-CODE-02",
        input_mode="artifact_path",
        fixture_kind="png_code_inferred",
        filename="python-script-no-name.png",
        mime_type="image/png",
        preferred_output_format="txt",
        expected_output_format="txt",
        expected_suggested_paths=("hello_curio.py",),
        expected_textification_intent="Extract Python code and infer a safe .py filename from the script purpose.",
        ground_truth_text='DEF HELLO_CURIO():\n    RETURN "HELLO CURIO"\nPRINT(HELLO_CURIO())',
        preservation_requirements=("HELLO_CURIO", 'RETURN "HELLO CURIO"', "PRINT(HELLO_CURIO())"),
    ),
    TextifySmokeCase(
        case_id="C-IMG-MULTI-01",
        input_mode="artifact_path",
        fixture_kind="png_multi_shell",
        filename="three-shell-scripts.png",
        mime_type="image/png",
        preferred_output_format="txt",
        expected_output_format="txt",
        expected_suggested_paths=("scripts/setup.sh", "scripts/run.sh", "scripts/cleanup.sh"),
        expected_textification_intent="Split three visible shell script snippets into three safe relative .sh files.",
        ground_truth_text=(
            "FILE: scripts/setup.sh\n"
            "ECHO SETUP\n\n"
            "FILE: scripts/run.sh\n"
            "ECHO RUN\n\n"
            "FILE: scripts/cleanup.sh\n"
            "ECHO CLEANUP"
        ),
        preservation_requirements=("scripts/setup.sh", "scripts/run.sh", "scripts/cleanup.sh", "ECHO CLEANUP"),
    ),
    TextifySmokeCase(
        case_id="C-IMG-POST-01",
        input_mode="artifact_path",
        fixture_kind="png_social",
        filename="social-post-es.png",
        mime_type="image/png",
        preferred_output_format="markdown",
        expected_output_format="markdown",
        expected_suggested_paths=("social-post.md",),
        expected_textification_intent="Preserve a social post's handle, timestamp, URL, emoji marker, and source language.",
        ground_truth_text="@MARIA 2026-04-27 10:15\nNO TRADUZCAS /V1/CHAT\nVISITA HTTPS://EXAMPLE.COM\nEMOJI: ROCKET",
        preservation_requirements=("@MARIA", "2026-04-27 10:15", "/V1/CHAT", "HTTPS://EXAMPLE.COM", "ROCKET"),
        source_language_hint="es",
    ),
    TextifySmokeCase(
        case_id="C-PDF-DOC-01",
        input_mode="artifact_path",
        fixture_kind="pdf_doc",
        filename="document-layout.pdf",
        mime_type="application/pdf",
        preferred_output_format="markdown",
        expected_output_format="markdown",
        expected_suggested_paths=("document.md",),
        expected_textification_intent="Extract a one-page document with title, headings, paragraphs, and bullets.",
        ground_truth_text="Curio Release Plan\nGoals\n- Keep smoke tests opt-in\n- Preserve source language\nNext Steps\nRun make check",
        preservation_requirements=("Curio Release Plan", "Goals", "Keep smoke tests opt-in", "Run make check"),
    ),
    TextifySmokeCase(
        case_id="C-PDF-TABLE-01",
        input_mode="artifact_path",
        fixture_kind="pdf_table",
        filename="table-layout.pdf",
        mime_type="application/pdf",
        preferred_output_format="markdown",
        expected_output_format="markdown",
        expected_suggested_paths=("table.md",),
        expected_textification_intent="Extract a small table without swapping rows or columns.",
        ground_truth_text="Service | Count | Status\nCodex | 3 | Ready\nDocAI | 1 | Punted\nOpenAI API | 0 | Punted",
        preservation_requirements=("Codex | 3 | Ready", "DocAI | 1 | Punted", "OpenAI API | 0 | Punted"),
    ),
    TextifySmokeCase(
        case_id="C-IMG-RECEIPT-01",
        input_mode="artifact_path",
        fixture_kind="png_receipt",
        filename="receipt.png",
        mime_type="image/png",
        preferred_output_format="markdown",
        expected_output_format="markdown",
        expected_suggested_paths=("receipt.md",),
        expected_textification_intent="Extract dense receipt-like labels, dates, amounts, and totals.",
        ground_truth_text="CURIO CAFE\nDATE 2026-04-27\nLATTE 4.50\nSANDWICH 8.25\nTOTAL 12.75",
        preservation_requirements=("2026-04-27", "LATTE 4.50", "SANDWICH 8.25", "TOTAL 12.75"),
    ),
    TextifySmokeCase(
        case_id="C-IMG-NO-TEXT-01",
        input_mode="artifact_path",
        fixture_kind="png_no_text",
        filename="no-readable-text.png",
        mime_type="image/png",
        preferred_output_format="markdown",
        expected_output_format="markdown",
        expected_suggested_paths=(),
        expected_textification_intent="Return no_text_found for an image with no readable text and do not invent alt text.",
        ground_truth_text="",
        preservation_requirements=("no invented description", "compact warning"),
        expected_status="no_text_found",
    ),
)

TEXTIFY_NOOP_SMOKE_CASE = TextifySmokeCase(
    case_id="C-TEXT-NOOP-01",
    input_mode="artifact_path",
    fixture_kind="text_noop",
    filename="already-text.txt",
    mime_type="text/plain",
    preferred_output_format="txt",
    expected_output_format="txt",
    expected_suggested_paths=(),
    expected_textification_intent="Skip an already-text source without calling an LLM.",
    ground_truth_text="ALREADY TEXT\nNO TEXTIFY NEEDED\n",
    preservation_requirements=("skipped_text_media", "no provider call"),
    participates_in_model_ranking=False,
    expect_llm_call=False,
    expected_status="skipped_text_media",
)


def _load_checked_in_smoke_cases() -> tuple[TextifySmokeCase, ...]:
    payload = json.loads(TEXTIFY_SMOKE_FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    if payload.get("version") != 1:
        raise TextifySmokeHarnessError("textify smoke fixture manifest version must be 1")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise TextifySmokeHarnessError("textify smoke fixture manifest cases must be a list")
    return tuple(_smoke_case_from_manifest_case(case_payload) for case_payload in cases)


def _smoke_case_from_manifest_case(payload: MappingPayload) -> TextifySmokeCase:
    fixture_path = _require_string_field(payload, "fixture_path")
    return TextifySmokeCase(
        case_id=_require_string_field(payload, "case_id"),
        input_mode=_require_string_field(payload, "input_mode"),
        fixture_kind=_require_string_field(payload, "fixture_kind"),
        filename=Path(fixture_path).name,
        mime_type=_require_string_field(payload, "mime_type"),
        preferred_output_format=_require_string_field(payload, "preferred_output_format"),
        expected_output_format=_require_string_field(payload, "expected_output_format"),
        expected_suggested_paths=_require_string_tuple(payload, "expected_suggested_paths"),
        expected_textification_intent=_require_string_field(payload, "expected_textification_intent"),
        ground_truth_text=_require_string_field(payload, "ground_truth_text"),
        preservation_requirements=_require_string_tuple(payload, "preservation_requirements"),
        source_language_hint=_optional_string_field(payload, "source_language_hint"),
        model_importance=_require_int_field(payload, "model_importance"),
        participates_in_model_ranking=_require_bool_field(payload, "participates_in_model_ranking"),
        expect_llm_call=_require_bool_field(payload, "expect_llm_call"),
        expected_status=_require_string_field(payload, "expected_status"),
        fixture_path=fixture_path,
        source_basenames=_require_string_tuple(payload, "source_basenames"),
        fixture_sha256=_require_string_field(payload, "sha256"),
    )


def _require_string_field(payload: MappingPayload, field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise TextifySmokeHarnessError(f"textify smoke fixture manifest {field_name} must be a string")
    return value


def _optional_string_field(payload: MappingPayload, field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TextifySmokeHarnessError(f"textify smoke fixture manifest {field_name} must be a string")
    return value


def _require_string_tuple(payload: MappingPayload, field_name: str) -> tuple[str, ...]:
    value = payload.get(field_name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TextifySmokeHarnessError(f"textify smoke fixture manifest {field_name} must be a string list")
    return tuple(value)


def _require_bool_field(payload: MappingPayload, field_name: str) -> bool:
    value = payload.get(field_name)
    if not isinstance(value, bool):
        raise TextifySmokeHarnessError(f"textify smoke fixture manifest {field_name} must be a bool")
    return value


def _require_int_field(payload: MappingPayload, field_name: str) -> int:
    value = payload.get(field_name)
    if not isinstance(value, int):
        raise TextifySmokeHarnessError(f"textify smoke fixture manifest {field_name} must be an int")
    return value


TEXTIFY_SMOKE_CASES = GENERATED_TEXTIFY_SMOKE_CASES + _load_checked_in_smoke_cases()


def select_codex_textify_caller(
    config_path: Path,
    llm_caller: str | None = None,
) -> tuple[CurioConfig, LlmCallerConfig]:
    try:
        config = load_config(config_path)
        caller_name = llm_caller if llm_caller is not None else config.textify_config.llm_caller
        if caller_name is None:
            raise TextifySmokeHarnessError("textify.llm_caller must be configured or --llm-caller must be provided")
        caller_config = config.llm_caller_config(caller_name)
    except ConfigError as exc:
        raise TextifySmokeHarnessError(str(exc)) from exc
    provider = cast(ProviderName, caller_config.provider)
    if provider != ProviderName.CODEX_CLI:
        raise TextifySmokeHarnessError(f"llm caller {caller_config.name} must use codex_cli for textify smoke tests")
    if caller_config.prompt_config is None:
        raise TextifySmokeHarnessError(f"llm caller {caller_config.name} must define a textify prompt")
    return config, caller_config


def build_smoke_textify_service(llm_client: LlmClient, caller_config: LlmCallerConfig) -> TextifyService:
    return TextifyService(
        llm_client=llm_client,
        prompt_config=caller_config.prompt_config,
        pricing_config=caller_config.pricing_config,
    )


def write_textify_smoke_fixture(case: TextifySmokeCase, run_root: Path) -> TextifySource:
    case_dir = run_root / "cases" / case.case_id
    fixture_dir = case_dir / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "expected.md").write_text(_expected_markdown(case), encoding="utf-8")
    path = fixture_dir / case.filename
    if case.fixture_path is not None:
        shutil.copyfile(TEXTIFY_SMOKE_FIXTURE_ROOT / case.fixture_path, path)
    elif case.fixture_kind == "text_noop":
        path.write_text(case.ground_truth_text, encoding="utf-8")
    elif case.fixture_kind.startswith("png_"):
        if case.fixture_kind == "png_no_text":
            _write_no_text_png(path)
        else:
            _write_png_text_fixture(path, case.ground_truth_text.splitlines())
    elif case.fixture_kind.startswith("pdf_"):
        _write_pdf_fixture(path, case.ground_truth_text.splitlines())
    else:
        raise TextifySmokeHarnessError(f"unknown fixture kind: {case.fixture_kind}")
    return _source_for_path(
        name=case.filename,
        path=path,
        mime_type=case.mime_type,
        source_language_hint=case.source_language_hint,
        context=_case_context(case),
    )


def build_textify_smoke_request(
    case: TextifySmokeCase,
    caller: str,
    source: TextifySource,
) -> TextifyRequest:
    return TextifyRequest(
        request_id=f"textify-smoke-{case.case_id}-{caller}",
        preferred_output_format=case.preferred_output_format,
        source=source,
        llm_caller=caller,
    )


def render_textified_output(response: TextifyResponse) -> str:
    return "\n\n".join(suggested_file.text for suggested_file in response.source.suggested_files)


def api_equivalent_cost_usd(usage: LlmUsage, pricing: ModelPricing) -> float | None:
    estimate = estimate_llm_cost(usage, pricing)
    return None if estimate is None else estimate.amount


def usage_payload(usage: LlmUsage, pricing: ModelPricing) -> JsonObject:
    return {
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": usage.cached_input_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_tokens": usage.reasoning_tokens,
        "total_tokens": usage.total_tokens,
        "metered_objects": [
            {"name": item.name, "quantity": item.quantity, "unit": item.unit} for item in usage.metered_objects
        ],
        "started_at": usage.started_at,
        "completed_at": usage.completed_at,
        "wall_seconds": usage.wall_seconds,
        "thinking_seconds": usage.thinking_seconds,
        "currency": pricing.currency,
        "basis": pricing.basis,
        "input_price_per_million": pricing.input_price_per_million,
        "cached_input_price_per_million": pricing.cached_input_price_per_million,
        "output_price_per_million": pricing.output_price_per_million,
        "api_equivalent_cost_usd": api_equivalent_cost_usd(usage, pricing),
    }


def redacted_caller_summary(caller_config: LlmCallerConfig) -> JsonObject:
    provider = cast(ProviderName, caller_config.provider)
    payload: JsonObject = {
        "name": caller_config.name,
        "provider": provider.value,
        "model": caller_config.model,
        "timeout_seconds": caller_config.timeout_seconds,
        "has_prompt_instructions": caller_config.prompt_config is not None
        and caller_config.prompt_config.instructions is not None,
        "has_prompt_user": caller_config.prompt_config is not None and caller_config.prompt_config.user is not None,
    }
    if caller_config.codex_exec_config is not None:
        payload["exec"] = _redacted_codex_exec_config(caller_config.codex_exec_config)
    return payload


def fixture_metadata(source: TextifySource) -> JsonObject:
    return {
        "name": source.name,
        "path": source.path,
        "mime_type": source.mime_type,
        "sha256": source.sha256,
        "source_language_hint": source.source_language_hint,
    }


def evaluator_input_record(
    *,
    case: TextifySmokeCase,
    caller_config: LlmCallerConfig,
    source: TextifySource,
    response: TextifyResponse,
    run_root: Path,
    pricing: ModelPricing,
) -> JsonObject:
    response_path = _run_path(run_root, case.case_id, caller_config.name) / "response.json"
    return {
        "case_id": case.case_id,
        "caller": caller_config.name,
        "fixture_metadata": fixture_metadata(source),
        "expected_textification_intent": case.expected_textification_intent,
        "ground_truth_text": case.ground_truth_text,
        "expected_output_format": case.expected_output_format,
        "expected_suggested_paths": list(case.expected_suggested_paths),
        "expected_status": case.expected_status,
        "model_importance": case.model_importance,
        "participates_in_model_ranking": case.participates_in_model_ranking,
        "preservation_requirements": list(case.preservation_requirements),
        "status": response.source.status.value,
        "output_format": [suggested_file.output_format for suggested_file in response.source.suggested_files],
        "suggested_files": [suggested_file.to_json() for suggested_file in response.source.suggested_files],
        "rendered_textified_text": render_textified_output(response),
        "response_warnings": _response_warnings(response),
        "usage": None if response.llm is None else usage_payload(response.llm.usage, pricing),
        "response_path": str(response_path.relative_to(run_root)),
    }


def write_textify_smoke_artifacts(
    *,
    run_root: Path,
    case: TextifySmokeCase,
    caller_config: LlmCallerConfig,
    source: TextifySource,
    request: TextifyRequest,
    response: TextifyResponse,
    pricing: ModelPricing,
    stderr: str = "",
) -> JsonObject:
    run_dir = _run_path(run_root, case.case_id, caller_config.name)
    evaluation_dir = run_root / "evaluation"
    run_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "request.json", request.to_json())
    _write_json(run_dir / "response.json", response.to_json())
    rendered = render_textified_output(response)
    (run_dir / _textified_filename(response)).write_text(rendered, encoding="utf-8")
    if response.llm is not None:
        _write_json(run_dir / "usage.json", usage_payload(response.llm.usage, pricing))
    if stderr:
        (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    record = evaluator_input_record(
        case=case,
        caller_config=caller_config,
        source=source,
        response=response,
        run_root=run_root,
        pricing=pricing,
    )
    with (evaluation_dir / "evaluator-input.jsonl").open("a", encoding="utf-8") as evaluator_input:
        evaluator_input.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        evaluator_input.write("\n")
    return record


def write_json(path: Path, payload: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _source_for_path(
    *,
    name: str,
    path: Path,
    mime_type: str,
    source_language_hint: str | None,
    context: JsonObject,
) -> TextifySource:
    return TextifySource(
        path=str(path.resolve()),
        name=name,
        mime_type=mime_type,
        sha256=file_sha256(path),
        source_language_hint=source_language_hint,
        context=context,
    )


def _case_context(case: TextifySmokeCase) -> JsonObject:
    return {
        "case_id": case.case_id,
        "expected_textification_intent": case.expected_textification_intent,
        "expected_output_format": case.expected_output_format,
        "expected_suggested_paths": list(case.expected_suggested_paths),
    }


def _run_path(run_root: Path, case_id: str, caller_name: str) -> Path:
    return run_root / "runs" / case_id / caller_name


def _response_warnings(response: TextifyResponse) -> list[str]:
    warnings = list(response.warnings)
    warnings.extend(response.source.warnings)
    return warnings


def _require_llm_usage(response: TextifyResponse) -> LlmUsage:
    if response.llm is None:
        raise TextifySmokeHarnessError("textify smoke response must include llm usage")
    return response.llm.usage


def _textified_filename(response: TextifyResponse) -> str:
    suggested_files = list(response.source.suggested_files)
    if len(suggested_files) == 1 and suggested_files[0].output_format == "txt":
        return "textified.txt"
    return "textified.md"


def _expected_markdown(case: TextifySmokeCase) -> str:
    paths = "\n".join(f"- {path}" for path in case.expected_suggested_paths) or "- none"
    requirements = "\n".join(f"- {requirement}" for requirement in case.preservation_requirements)
    return "\n".join(
        (
            f"# {case.case_id}",
            "",
            "## Expected Textification Intent",
            "",
            case.expected_textification_intent,
            "",
            "## Expected Suggested Paths",
            "",
            paths,
            "",
            "## Model Importance",
            "",
            str(case.model_importance),
            "",
            "## Model Ranking",
            "",
            "included" if case.participates_in_model_ranking else "coverage-only",
            "",
            "## Preservation Requirements",
            "",
            requirements,
            "",
            "## Ground Truth Text",
            "",
            "```text",
            case.ground_truth_text,
            "```",
            "",
        )
    )


def _redacted_codex_exec_config(config: CodexCliExecConfig) -> JsonObject:
    return {
        "executable": config.executable,
        "sandbox": config.sandbox,
        "color": config.color,
        "ephemeral": config.ephemeral,
        "json_events": config.json_events,
        "skip_git_repo_check": config.skip_git_repo_check,
        "ignore_user_config": config.ignore_user_config,
        "model_reasoning_effort": None if config.model_reasoning_effort is None else config.model_reasoning_effort.value,
        "model_verbosity": None if config.model_verbosity is None else config.model_verbosity.value,
        "extra_config": list(config.extra_config),
    }


def _write_json(path: Path, payload: MappingPayload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_png_text_fixture(path: Path, lines: list[str]) -> None:
    normalized_lines = [line.upper() for line in lines] or [""]
    scale = 3
    padding = 12
    glyph_width = 5
    glyph_height = 7
    glyph_gap = 2
    line_gap = 5
    columns = max(len(line) for line in normalized_lines)
    width = padding * 2 + max(1, columns) * (glyph_width + glyph_gap) * scale
    height = padding * 2 + len(normalized_lines) * (glyph_height * scale + line_gap)
    pixels = bytearray([255] * width * height * 3)
    for line_index, line in enumerate(normalized_lines):
        y = padding + line_index * (glyph_height * scale + line_gap)
        _draw_text_line(pixels, width, height, padding, y, line, scale)
    _write_png(path, width, height, bytes(pixels))


def _write_no_text_png(path: Path) -> None:
    width = 240
    height = 160
    pixels = bytearray()
    for y in range(height):
        for x in range(width):
            red = int(120 + 80 * math.sin(x / 21))
            green = int(140 + 70 * math.sin(y / 17))
            blue = int(160 + 50 * math.sin((x + y) / 31))
            pixels.extend((red, green, blue))
    _write_png(path, width, height, bytes(pixels))


def _draw_text_line(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    text: str,
    scale: int,
) -> None:
    cursor = x
    for char in text:
        pattern = _FONT.get(char, _FONT["?"])
        for row_index, row in enumerate(pattern):
            for column_index, value in enumerate(row):
                if value == "1":
                    _fill_rect(
                        pixels,
                        width,
                        height,
                        cursor + column_index * scale,
                        y + row_index * scale,
                        scale,
                        scale,
                        (0, 0, 0),
                    )
        cursor += (5 + 2) * scale


def _fill_rect(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    rect_width: int,
    rect_height: int,
    color: tuple[int, int, int],
) -> None:
    red, green, blue = color
    for yy in range(max(0, y), min(height, y + rect_height)):
        for xx in range(max(0, x), min(width, x + rect_width)):
            offset = (yy * width + xx) * 3
            pixels[offset : offset + 3] = bytes((red, green, blue))


def _write_png(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stride = width * 3
    raw = b"".join(b"\x00" + rgb[y * stride : (y + 1) * stride] for y in range(height))
    chunks = [
        _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
        _png_chunk(b"IDAT", zlib.compress(raw)),
        _png_chunk(b"IEND", b""),
    ]
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"".join(chunks))


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(data, checksum)
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum & 0xFFFFFFFF)


def _write_pdf_fixture(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_lines = ["BT", "/F1 14 Tf", "72 740 Td", "18 TL"]
    for line in lines:
        content_lines.append(f"({_pdf_escape(line)}) Tj")
        content_lines.append("T*")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(output))


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


_FONT = {
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "#": ("01010", "11111", "01010", "01010", "11111", "01010", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "%": ("11001", "11010", "00100", "01000", "10110", "00110", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    "/": ("00001", "00010", "00100", "01000", "10000", "00000", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ":": ("00000", "00110", "00110", "00000", "00110", "00110", "00000"),
    ";": ("00000", "00110", "00110", "00000", "00110", "00100", "01000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "=": ("00000", "11111", "00000", "11111", "00000", "00000", "00000"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10111", "10000", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "\\": ("10000", "01000", "00100", "00010", "00001", "00000", "00000"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "{": ("00010", "00100", "00100", "01000", "00100", "00100", "00010"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "}": ("01000", "00100", "00100", "00010", "00100", "00100", "01000"),
}
