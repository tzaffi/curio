import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from curio.cli import app
from textify_smoke_helpers import (
    DEFAULT_TEXTIFY_SMOKE_ROOT,
    TEXTIFY_SMOKE_CALLERS,
    TEXTIFY_SMOKE_CASES,
    build_textify_smoke_request,
    evaluator_record,
    write_json,
    write_placeholder_png,
)

runner = CliRunner()


@pytest.mark.live_codex_cli_textify
@pytest.mark.parametrize("case", TEXTIFY_SMOKE_CASES)
@pytest.mark.parametrize("caller", TEXTIFY_SMOKE_CALLERS)
def test_live_codex_cli_textify_case_matrix(case, caller, tmp_path: Path) -> None:
    run_id = os.environ.get("CURIO_TEXTIFY_SMOKE_RUN_ID", "manual")
    artifact_path = write_placeholder_png(tmp_path / case.filename)
    request = build_textify_smoke_request(case, caller, artifact_path)
    input_path = tmp_path / f"{case.case_id}-{caller}.json"
    write_json(input_path, request.to_json())

    result = runner.invoke(
        app,
        [
            "textify",
            "--input-json",
            str(input_path),
            "--config",
            str(Path(__file__).resolve().parents[1] / "config.example.codex_cli.json"),
            "--json",
        ],
    )

    run_root = DEFAULT_TEXTIFY_SMOKE_ROOT / run_id
    output_path = run_root / "responses" / f"{case.case_id}-{caller}.json"
    record_path = run_root / "evaluation" / "evaluator-input.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.output, encoding="utf-8")
    if result.exit_code == 0:
        with record_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(evaluator_record(case, caller, json.loads(result.output)), ensure_ascii=False) + "\n")
    assert result.exit_code == 0
