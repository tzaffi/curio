import json
from pathlib import Path

import pytest

from live_smoke_evaluator import (
    DEFAULT_EVALUATOR_MODEL,
    EvaluatorError,
    build_codex_evaluator_command,
    build_evaluator_prompt,
    prepare_evaluator_artifacts,
    resolve_run_root,
)


def make_run(tmp_path: Path, run_id: str = "20260426-000000-test") -> Path:
    run_root = tmp_path / run_id
    evaluation_dir = run_root / "evaluation"
    run_dir = run_root / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini"
    evaluation_dir.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    (run_root / "manifest.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    (run_dir / "usage.json").write_text(
        json.dumps(
            {
                "input_tokens": 100,
                "cached_input_tokens": 20,
                "output_tokens": 30,
                "reasoning_tokens": 5,
                "input_price_per_million": 0.75,
                "cached_input_price_per_million": 0.075,
                "output_price_per_million": 4.5,
                "api_equivalent_cost_usd": 0.0002115,
            }
        ),
        encoding="utf-8",
    )
    (evaluation_dir / "evaluator-input.jsonl").write_text(
        json.dumps(
            {
                "case_id": "C-JA-01",
                "caller": "translator_codex_gpt_54_mini",
                "source_text": "こんにちは",
                "expected_translation_intent": "Translate greeting.",
                "preservation_requirements": ["greeting"],
                "translation_required": True,
                "translated_text": "Hello.",
                "response_warnings": [],
                "usage": {"input_tokens": 100},
                "response_path": "runs/C-JA-01/translator_codex_gpt_54_mini/response.json",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_root


def test_prepare_evaluator_artifacts_adds_cost_payload_and_prompt(tmp_path: Path) -> None:
    run_root = make_run(tmp_path)

    artifacts = prepare_evaluator_artifacts(run_root)

    assert artifacts.record_count == 1
    assert artifacts.payload_path.exists()
    assert artifacts.prompt_path.exists()
    records = [
        json.loads(line)
        for line in artifacts.evaluator_input_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert records[0]["cost"] == 0.0002115
    assert records[0]["usage"]["api_equivalent_cost_usd"] == 0.0002115
    payload = json.loads(artifacts.payload_path.read_text(encoding="utf-8"))
    assert payload["record_count"] == 1
    assert payload["manifest"] == {"run_id": "20260426-000000-test"}
    prompt = artifacts.prompt_path.read_text(encoding="utf-8")
    assert "Evaluator model requirement: Codex ChatGPT 5.5, Extra High reasoning effort." in prompt
    assert "C-JA-01" in prompt


def test_build_evaluator_prompt_contains_required_matrix_contract() -> None:
    prompt = build_evaluator_prompt({"record_count": 0, "records": []})

    assert "| Case ID | Caller | Cost | Adequacy | Fluency | Preservation | Instruction Following |" in prompt
    assert "Break quality ties by lower cost." in prompt


def test_build_codex_evaluator_command_uses_gpt55_xhigh_defaults(tmp_path: Path) -> None:
    artifacts = prepare_evaluator_artifacts(make_run(tmp_path))

    command = build_codex_evaluator_command(artifacts)

    assert command[:2] == ["codex", "exec"]
    assert "--json" in command
    assert command[command.index("--model") + 1] == DEFAULT_EVALUATOR_MODEL
    assert 'model_reasoning_effort="xhigh"' in command
    assert 'model_verbosity="medium"' in command
    assert command[command.index("--output-last-message") + 1] == str(artifacts.output_path)
    assert command[-1] == "-"


def test_resolve_run_root_accepts_latest_and_explicit_paths(tmp_path: Path) -> None:
    older = make_run(tmp_path, "20260426-000000-old")
    newer = make_run(tmp_path, "20260426-000001-new")

    assert resolve_run_root("latest", smoke_root=tmp_path) == newer
    assert resolve_run_root(str(older)) == older


def test_prepare_evaluator_artifacts_reports_invalid_input(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(EvaluatorError, match="missing evaluator input"):
        resolve_run_root(str(missing))

    run_root = make_run(tmp_path)
    (run_root / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini" / "usage.json").write_text(
        json.dumps({"api_equivalent_cost_usd": "bad"}),
        encoding="utf-8",
    )
    with pytest.raises(EvaluatorError, match="api_equivalent_cost_usd"):
        prepare_evaluator_artifacts(run_root)
