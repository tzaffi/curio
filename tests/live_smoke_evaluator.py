import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SMOKE_ROOT = REPO_ROOT / "tmp" / "translate-smoke"
DEFAULT_EVALUATOR_MODEL = "gpt-5.5"
DEFAULT_EVALUATOR_REASONING_EFFORT = "xhigh"
DEFAULT_EVALUATOR_VERBOSITY = "medium"

EVALUATOR_PROMPT_TEMPLATE = """You are the Checkpoint 8G translation evaluator for Curio.

Use only the JSON payload in this prompt. Do not browse. Do not run commands. Do not judge whether the source claims, politics, sentiment, profanity, or style are desirable; judge only translation fidelity and instruction following.

Evaluator model requirement: Codex ChatGPT 5.5, Extra High reasoning effort.

Task:
- Grade each translation output row in the payload.
- Scores are integers 1-5.
- Adequacy: source meaning captured.
- Fluency: natural target English.
- Preservation: URLs, commands, handles, filenames, code identifiers, names, numbers, quotes, tone, and requested artifacts preserved.
- Instruction Following: schema intent, pass-through behavior, no additions/sanitization/escalation, warnings used appropriately.
- Total is the sum of Adequacy + Fluency + Preservation + Instruction Following.
- Cost must be the exact `cost` value from each record, formatted with enough precision to distinguish rows.
- For each Case ID, mark exactly one row Preferred? = yes unless all three caller outputs are unusable; otherwise mark no. Break quality ties by lower cost.
- For offensive or political source text, preserve fidelity as the scoring criterion and flag unnecessary sanitization, escalation, or added context.
- For English pass-through, a correct output should have translation_required=false and preserve the original text.

Return Markdown only, with these sections:

## Evaluator Summary
A concise paragraph covering overall quality, preferred caller pattern, and any notable risks.

## Evaluator Output Matrix
A Markdown table with exactly these columns:
| Case ID | Caller | Cost | Adequacy | Fluency | Preservation | Instruction Following | Total | Preferred? | Warnings / Failures | Evaluator Notes |

## Per-Case Preference Notes
One bullet per case explaining why the preferred caller won and whether cost decided a tie.

Payload:
```json
{payload_json}
```
"""


@dataclass(frozen=True, slots=True)
class EvaluatorArtifacts:
    run_root: Path
    evaluator_input_path: Path
    payload_path: Path
    prompt_path: Path
    output_path: Path
    events_path: Path
    record_count: int


class EvaluatorError(RuntimeError):
    pass


def resolve_run_root(run_root: str, *, smoke_root: Path = DEFAULT_SMOKE_ROOT) -> Path:
    if run_root == "latest":
        runs = sorted(path for path in smoke_root.iterdir() if (path / "evaluation" / "evaluator-input.jsonl").exists())
        if not runs:
            raise EvaluatorError(f"no smoke runs with evaluator input found under {smoke_root}")
        return runs[-1]
    path = Path(run_root)
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not (path / "evaluation" / "evaluator-input.jsonl").exists():
        raise EvaluatorError(f"missing evaluator input at {path / 'evaluation' / 'evaluator-input.jsonl'}")
    return path


def prepare_evaluator_artifacts(run_root: Path) -> EvaluatorArtifacts:
    evaluation_dir = run_root / "evaluation"
    evaluator_input_path = evaluation_dir / "evaluator-input.jsonl"
    records = [_with_cost_from_usage(run_root, record) for record in _read_jsonl(evaluator_input_path)]
    if not records:
        raise EvaluatorError(f"no evaluator records found in {evaluator_input_path}")
    _write_jsonl(evaluator_input_path, records)
    payload = {
        "run_root": str(run_root),
        "record_count": len(records),
        "manifest": _read_optional_json(run_root / "manifest.json"),
        "records": records,
    }
    payload_path = evaluation_dir / "evaluator-payload.json"
    prompt_path = evaluation_dir / "evaluator-prompt.md"
    output_path = evaluation_dir / "evaluator-output.md"
    events_path = evaluation_dir / "evaluator-run.jsonl"
    _write_json(payload_path, payload)
    prompt_path.write_text(build_evaluator_prompt(payload), encoding="utf-8")
    return EvaluatorArtifacts(
        run_root=run_root,
        evaluator_input_path=evaluator_input_path,
        payload_path=payload_path,
        prompt_path=prompt_path,
        output_path=output_path,
        events_path=events_path,
        record_count=len(records),
    )


def build_evaluator_prompt(payload: JsonObject) -> str:
    return EVALUATOR_PROMPT_TEMPLATE.format(
        payload_json=json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    )


def build_codex_evaluator_command(
    artifacts: EvaluatorArtifacts,
    *,
    model: str = DEFAULT_EVALUATOR_MODEL,
    reasoning_effort: str = DEFAULT_EVALUATOR_REASONING_EFFORT,
    verbosity: str = DEFAULT_EVALUATOR_VERBOSITY,
) -> list[str]:
    return [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--cd",
        str(REPO_ROOT),
        "--config",
        f'model_reasoning_effort="{reasoning_effort}"',
        "--config",
        f'model_verbosity="{verbosity}"',
        "--model",
        model,
        "--output-last-message",
        str(artifacts.output_path),
        "-",
    ]


def run_codex_evaluator(
    artifacts: EvaluatorArtifacts,
    *,
    model: str = DEFAULT_EVALUATOR_MODEL,
    reasoning_effort: str = DEFAULT_EVALUATOR_REASONING_EFFORT,
    verbosity: str = DEFAULT_EVALUATOR_VERBOSITY,
) -> int:
    command = build_codex_evaluator_command(
        artifacts,
        model=model,
        reasoning_effort=reasoning_effort,
        verbosity=verbosity,
    )
    with artifacts.prompt_path.open("r", encoding="utf-8") as stdin:
        with artifacts.events_path.open("w", encoding="utf-8") as stdout:
            completed = subprocess.run(command, stdin=stdin, stdout=stdout, text=True, check=False)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare and run the Curio translation smoke evaluator.")
    parser.add_argument(
        "run_root",
        nargs="?",
        default="latest",
        help="Smoke run root, or 'latest' for the newest run with evaluator input.",
    )
    parser.add_argument("--prepare-only", action="store_true", help="Write evaluator payload/prompt without running Codex.")
    parser.add_argument("--model", default=DEFAULT_EVALUATOR_MODEL)
    parser.add_argument("--reasoning-effort", default=DEFAULT_EVALUATOR_REASONING_EFFORT)
    parser.add_argument("--verbosity", default=DEFAULT_EVALUATOR_VERBOSITY)
    args = parser.parse_args(argv)

    run_root = resolve_run_root(args.run_root)
    artifacts = prepare_evaluator_artifacts(run_root)
    print(f"prepared {artifacts.record_count} evaluator records")
    print(f"prompt: {artifacts.prompt_path}")
    print(f"payload: {artifacts.payload_path}")
    if args.prepare_only:
        return 0
    return_code = run_codex_evaluator(
        artifacts,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        verbosity=args.verbosity,
    )
    print(f"events: {artifacts.events_path}")
    print(f"output: {artifacts.output_path}")
    return return_code


def _with_cost_from_usage(run_root: Path, record: JsonObject) -> JsonObject:
    current = dict(record)
    response_path = run_root / _require_string(current.get("response_path"), "response_path")
    usage_path = response_path.parent / "usage.json"
    usage = _read_json(usage_path)
    cost = usage.get("api_equivalent_cost_usd")
    if not isinstance(cost, int | float) or isinstance(cost, bool):
        raise EvaluatorError(f"missing numeric api_equivalent_cost_usd in {usage_path}")
    current["usage"] = usage
    current["cost"] = cost
    return current


def _read_jsonl(path: Path) -> list[JsonObject]:
    records: list[JsonObject] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise EvaluatorError(f"{path}:{line_number} must contain a JSON object")
        records.append(value)
    return records


def _write_jsonl(path: Path, records: list[JsonObject]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> JsonObject:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvaluatorError(f"{path} must contain a JSON object")
    return value


def _read_optional_json(path: Path) -> JsonObject | None:
    return None if not path.exists() else _read_json(path)


def _write_json(path: Path, payload: JsonObject) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluatorError(f"{name} must be a non-empty string")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
