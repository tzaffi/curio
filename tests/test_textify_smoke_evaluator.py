import json
from pathlib import Path

from textify_smoke_evaluator import (
    EXPECTED_EVALUATOR_RECORD_COUNT,
    prepare_evaluator_artifacts,
    publish_report_artifacts,
    resolve_run_root,
)


def test_textify_publish_report_artifacts_copies_evaluator_files(tmp_path: Path) -> None:
    run_root = tmp_path / "tmp" / "textify-smoke" / "run-1"
    evaluation_dir = run_root / "evaluation"
    evaluation_dir.mkdir(parents=True)
    (run_root / "manifest.json").write_text('{"run": "run-1"}\n', encoding="utf-8")
    (evaluation_dir / "evaluator-input.jsonl").write_text(
        json.dumps({"case_id": "C-IMG-TXT-01", "caller": "textifier_codex_gpt_54_mini"}) + "\n",
        encoding="utf-8",
    )
    artifacts = prepare_evaluator_artifacts(run_root)
    artifacts.output_path.write_text("## Evaluator Output\n", encoding="utf-8")
    artifacts.events_path.write_text('{"type":"turn.completed"}\n', encoding="utf-8")

    report_dir = publish_report_artifacts(artifacts, report_root=tmp_path / "reports")

    assert report_dir == tmp_path / "reports" / "run-1"
    assert (report_dir / "README.md").read_text(encoding="utf-8").startswith("# Textify Smoke Report run-1")
    assert (report_dir / "manifest.json").read_text(encoding="utf-8") == '{"run": "run-1"}\n'
    assert (report_dir / "evaluator-input.jsonl").exists()
    assert (report_dir / "evaluator-output.md").read_text(encoding="utf-8") == "## Evaluator Output\n"
    assert (report_dir / "evaluator-payload.json").exists()
    assert (report_dir / "evaluator-prompt.md").exists()
    assert (report_dir / "evaluator-run.jsonl").read_text(encoding="utf-8") == '{"type":"turn.completed"}\n'


def test_textify_resolve_latest_prefers_complete_matrix_over_targeted_runs(tmp_path: Path) -> None:
    smoke_root = tmp_path / "tmp" / "textify-smoke"
    complete = smoke_root / "20260428-010000-complete"
    targeted = smoke_root / "20260428-020000-targeted"
    _write_evaluator_input(complete, EXPECTED_EVALUATOR_RECORD_COUNT)
    _write_evaluator_input(targeted, 3)

    assert resolve_run_root("latest", smoke_root=smoke_root) == complete


def _write_evaluator_input(run_root: Path, count: int) -> None:
    evaluation_dir = run_root / "evaluation"
    evaluation_dir.mkdir(parents=True)
    payload = {"case_id": "C-IMG-TXT-01", "caller": "textifier_codex_gpt_54_mini"}
    (evaluation_dir / "evaluator-input.jsonl").write_text(
        "".join(json.dumps(payload) + "\n" for _ in range(count)),
        encoding="utf-8",
    )
