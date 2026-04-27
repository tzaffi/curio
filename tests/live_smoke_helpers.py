import json
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
from curio.translate.models import JsonObject, TranslationRequest, TranslationResponse
from curio.translate.service import TranslationService

MappingPayload = dict[str, Any]


class SmokeHarnessError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SmokeCase:
    case_id: str
    source_text: str
    expected_translation_intent: str
    preservation_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_non_empty_string(self.case_id, "case_id")
        _require_non_empty_string(self.source_text, "source_text")
        _require_non_empty_string(self.expected_translation_intent, "expected_translation_intent")
        for requirement in self.preservation_requirements:
            _require_non_empty_string(requirement, "preservation requirement")


ModelPricing = LlmPricing


def select_codex_smoke_caller(
    config_path: Path,
    llm_caller: str | None = None,
) -> tuple[CurioConfig, LlmCallerConfig]:
    try:
        config = load_config(config_path)
        caller_name = llm_caller if llm_caller is not None else config.translate_config.llm_caller
        if caller_name is None:
            raise SmokeHarnessError("translate.llm_caller must be configured or --llm-caller must be provided")
        caller_config = config.llm_caller_config(caller_name)
    except ConfigError as exc:
        raise SmokeHarnessError(str(exc)) from exc
    provider = cast(ProviderName, caller_config.provider)
    if provider != ProviderName.CODEX_CLI:
        raise SmokeHarnessError(f"llm caller {caller_config.name} must use codex_cli for Codex live smoke tests")
    return config, caller_config


def build_smoke_translation_service(llm_client: LlmClient, caller_config: LlmCallerConfig) -> TranslationService:
    return TranslationService(
        llm_client=llm_client,
        prompt_config=caller_config.prompt_config,
        pricing_config=caller_config.pricing_config,
    )


def render_translation_text(request: TranslationRequest, response: TranslationResponse) -> str:
    source_by_id = {block.block_id: block.text for block in request.blocks}
    rendered_blocks: list[str] = []
    for block in response.blocks:
        if block.translation_required:
            rendered_blocks.append(cast(str, block.translated_text))
        else:
            rendered_blocks.append(source_by_id[block.block_id])
    return "\n\n".join(rendered_blocks)


def api_equivalent_cost_usd(usage: LlmUsage, pricing: ModelPricing) -> float | None:
    estimate = estimate_llm_cost(usage, pricing)
    return None if estimate is None else estimate.amount


def usage_payload(usage: LlmUsage, pricing: ModelPricing) -> JsonObject:
    return {
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": usage.cached_input_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_tokens": usage.reasoning_tokens,
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


def evaluator_input_record(
    *,
    case: SmokeCase,
    caller_config: LlmCallerConfig,
    request: TranslationRequest,
    response: TranslationResponse,
    run_root: Path,
    pricing: ModelPricing,
) -> JsonObject:
    response_path = _run_path(run_root, case.case_id, caller_config.name) / "response.json"
    return {
        "case_id": case.case_id,
        "caller": caller_config.name,
        "source_text": case.source_text,
        "expected_translation_intent": case.expected_translation_intent,
        "preservation_requirements": list(case.preservation_requirements),
        "translation_required": any(block.translation_required for block in response.blocks),
        "translated_text": render_translation_text(request, response),
        "response_warnings": _response_warnings(response),
        "usage": usage_payload(response.llm.usage, pricing),
        "response_path": str(response_path.relative_to(run_root)),
    }


def write_smoke_artifacts(
    *,
    run_root: Path,
    case: SmokeCase,
    caller_config: LlmCallerConfig,
    request: TranslationRequest,
    response: TranslationResponse,
    pricing: ModelPricing,
    stderr: str = "",
) -> JsonObject:
    case_dir = run_root / "cases" / case.case_id
    run_dir = _run_path(run_root, case.case_id, caller_config.name)
    evaluation_dir = run_root / "evaluation"
    case_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / "source.txt").write_text(case.source_text, encoding="utf-8")
    (case_dir / "expected.md").write_text(_expected_markdown(case), encoding="utf-8")
    _write_json(run_dir / "request.json", request.to_json())
    _write_json(run_dir / "response.json", response.to_json())
    (run_dir / "translated.txt").write_text(render_translation_text(request, response), encoding="utf-8")
    _write_json(run_dir / "usage.json", usage_payload(response.llm.usage, pricing))
    if stderr:
        (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")

    evaluator_record = evaluator_input_record(
        case=case,
        caller_config=caller_config,
        request=request,
        response=response,
        run_root=run_root,
        pricing=pricing,
    )
    evaluator_input_path = evaluation_dir / "evaluator-input.jsonl"
    with evaluator_input_path.open("a", encoding="utf-8") as evaluator_input:
        evaluator_input.write(json.dumps(evaluator_record, ensure_ascii=False, sort_keys=True))
        evaluator_input.write("\n")
    return evaluator_record


def _run_path(run_root: Path, case_id: str, caller_name: str) -> Path:
    return run_root / "runs" / case_id / caller_name


def _response_warnings(response: TranslationResponse) -> list[str]:
    warnings = list(response.warnings)
    for block in response.blocks:
        warnings.extend(block.warnings)
    return warnings


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


def _expected_markdown(case: SmokeCase) -> str:
    requirements = "\n".join(f"- {requirement}" for requirement in case.preservation_requirements)
    return "\n".join(
        (
            f"# {case.case_id}",
            "",
            "## Expected Translation Intent",
            "",
            case.expected_translation_intent,
            "",
            "## Preservation Requirements",
            "",
            requirements,
            "",
        )
    )


def _write_json(path: Path, payload: MappingPayload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _require_non_empty_string(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
