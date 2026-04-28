import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from textify_smoke_helpers import TEXTIFY_SMOKE_CALLERS, TEXTIFY_SMOKE_CASES

JsonObject = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SMOKE_ROOT = REPO_ROOT / "tmp" / "textify-smoke"
DEFAULT_REPORT_ROOT = REPO_ROOT / "reports" / "textify-smoke"
DEFAULT_EVALUATOR_MODEL = "gpt-5.5"
DEFAULT_EVALUATOR_REASONING_EFFORT = "xhigh"
DEFAULT_EVALUATOR_VERBOSITY = "medium"
EXPECTED_EVALUATOR_RECORD_COUNT = len(TEXTIFY_SMOKE_CASES) * len(TEXTIFY_SMOKE_CALLERS)

EVALUATOR_PROMPT_TEMPLATE = """You are the Checkpoint 8G textify evaluator for Curio.

Use only the JSON payload in this prompt. Do not browse. Do not run commands.
Judge OCR/text extraction fidelity, source-language preservation, suggested filenames/extensions/paths, multiple-file handling, warning quality, and cost.

Return Markdown only, with:

## Evaluator Summary

## Evaluator Output Matrix
| Case ID | Caller | Cost | Text Fidelity | Structure | Filenames | Instruction Following | Total | Preferred? | Warnings / Failures | Evaluator Notes |

## Final Recommendation

Payload:
```json
{payload_json}
```
"""


@dataclass(frozen=True, slots=True)
class TextifyEvaluatorArtifacts:
    run_root: Path
    evaluator_input_path: Path
    payload_path: Path
    prompt_path: Path
    output_path: Path
    events_path: Path
    record_count: int


class TextifyEvaluatorError(RuntimeError):
    pass


def resolve_run_root(run_root: str, *, smoke_root: Path = DEFAULT_SMOKE_ROOT) -> Path:
    if run_root == "latest":
        runs = sorted(
            path
            for path in smoke_root.iterdir()
            if _evaluator_record_count(path / "evaluation" / "evaluator-input.jsonl") == EXPECTED_EVALUATOR_RECORD_COUNT
        )
        if not runs:
            raise TextifyEvaluatorError(f"no complete textify smoke runs with evaluator input found under {smoke_root}")
        return runs[-1]
    path = Path(run_root)
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not (path / "evaluation" / "evaluator-input.jsonl").exists():
        raise TextifyEvaluatorError(f"missing evaluator input at {path / 'evaluation' / 'evaluator-input.jsonl'}")
    return path


def prepare_evaluator_artifacts(run_root: Path) -> TextifyEvaluatorArtifacts:
    evaluation_dir = run_root / "evaluation"
    evaluator_input_path = evaluation_dir / "evaluator-input.jsonl"
    records = _read_jsonl(evaluator_input_path)
    if not records:
        raise TextifyEvaluatorError(f"no evaluator records found in {evaluator_input_path}")
    payload = {"run_root": str(run_root), "record_count": len(records), "records": records}
    payload_path = evaluation_dir / "evaluator-payload.json"
    prompt_path = evaluation_dir / "evaluator-prompt.md"
    output_path = evaluation_dir / "evaluator-output.md"
    events_path = evaluation_dir / "evaluator-run.jsonl"
    _write_json(payload_path, payload)
    prompt_path.write_text(build_evaluator_prompt(payload), encoding="utf-8")
    return TextifyEvaluatorArtifacts(
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
    artifacts: TextifyEvaluatorArtifacts,
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


def run_codex_evaluator(artifacts: TextifyEvaluatorArtifacts) -> int:
    command = build_codex_evaluator_command(artifacts)
    with artifacts.prompt_path.open("r", encoding="utf-8") as stdin:
        with artifacts.events_path.open("w", encoding="utf-8") as stdout:
            completed = subprocess.run(command, stdin=stdin, stdout=stdout, text=True, check=False)
    return completed.returncode


def publish_report_artifacts(
    artifacts: TextifyEvaluatorArtifacts,
    *,
    report_root: Path = DEFAULT_REPORT_ROOT,
) -> Path:
    report_dir = report_root / artifacts.run_root.name
    report_dir.mkdir(parents=True, exist_ok=True)
    _copy_if_exists(artifacts.run_root / "manifest.json", report_dir / "manifest.json")
    _copy_if_exists(artifacts.evaluator_input_path, report_dir / "evaluator-input.jsonl")
    _copy_if_exists(artifacts.output_path, report_dir / "evaluator-output.md")
    _copy_if_exists(artifacts.payload_path, report_dir / "evaluator-payload.json")
    _copy_if_exists(artifacts.prompt_path, report_dir / "evaluator-prompt.md")
    _copy_if_exists(artifacts.events_path, report_dir / "evaluator-run.jsonl")
    (report_dir / "README.md").write_text(
        (
            f"# Textify Smoke Report {artifacts.run_root.name}\n\n"
            f"Records: {artifacts.record_count}\n\n"
            "- `UPSHOT.md`: caller recommendation, escalation policy, and known risks.\n"
            "- `evaluator-output.md`: evaluator scoring matrix and per-case preference notes.\n"
            "- `evaluator-input.jsonl`: compact row-oriented evaluator input.\n"
            "- `evaluator-payload.json`: normalized evaluator payload used for the run.\n"
            "- `evaluator-prompt.md`: exact evaluator prompt plus payload.\n"
            "- `evaluator-run.jsonl`: Codex evaluator event stream.\n"
            "- `manifest.json`: live smoke run metadata.\n"
        ),
        encoding="utf-8",
    )
    return report_dir


def _read_jsonl(path: Path) -> list[JsonObject]:
    records: list[JsonObject] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TextifyEvaluatorError(f"JSONL record in {path} must be an object")
            records.append(value)
    return records


def _evaluator_record_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _write_json(path: Path, payload: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    artifacts = prepare_evaluator_artifacts(resolve_run_root(args.run_root))
    if args.prepare_only:
        publish_report_artifacts(artifacts)
        return 0
    return run_codex_evaluator(artifacts)


if __name__ == "__main__":
    raise SystemExit(main())
