from pathlib import Path

from textify_smoke_helpers import (
    TEXTIFY_SMOKE_CALLERS,
    TEXTIFY_SMOKE_CASES,
    build_textify_smoke_request,
    evaluator_record,
    write_placeholder_png,
)


def test_textify_smoke_helpers_build_requests_and_records(tmp_path: Path) -> None:
    case = TEXTIFY_SMOKE_CASES[0]
    artifact_path = write_placeholder_png(tmp_path / case.filename)

    request = build_textify_smoke_request(case, TEXTIFY_SMOKE_CALLERS[0], artifact_path)
    record = evaluator_record(case, TEXTIFY_SMOKE_CALLERS[0], {"ok": True})

    assert request.llm_caller == "textifier_codex_gpt_55"
    assert request.artifacts[0].sha256 is not None
    assert record["case_id"] == case.case_id
    assert record["response"] == {"ok": True}
