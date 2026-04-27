import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from curio.textify import Artifact, TextifyRequest, file_sha256

JsonObject = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEXTIFY_SMOKE_ROOT = REPO_ROOT / "tmp" / "textify-smoke"
TEXTIFY_SMOKE_CALLERS = (
    "textifier_codex_gpt_55",
    "textifier_codex_gpt_54_mini",
    "textifier_codex_gpt_54_nano",
)

_ONE_PIXEL_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


@dataclass(frozen=True, slots=True)
class TextifySmokeCase:
    case_id: str
    filename: str
    mime_type: str
    expected_summary: str


TEXTIFY_SMOKE_CASES = (
    TextifySmokeCase(
        case_id="T-IMG-01",
        filename="receipt-ja.png",
        mime_type="image/png",
        expected_summary="image OCR should preserve source-language visible text",
    ),
    TextifySmokeCase(
        case_id="T-CODE-01",
        filename="python-script.png",
        mime_type="image/png",
        expected_summary="code screenshot should suggest a natural .py file",
    ),
)


def write_placeholder_png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(_ONE_PIXEL_PNG))
    return path


def build_textify_smoke_request(case: TextifySmokeCase, caller: str, artifact_path: Path) -> TextifyRequest:
    return TextifyRequest(
        request_id=f"textify-smoke-{case.case_id}-{caller}",
        artifacts=[
            Artifact(
                artifact_id=1,
                name=case.filename,
                path=str(artifact_path.resolve()),
                mime_type=case.mime_type,
                sha256=file_sha256(artifact_path),
                source_language_hint=None,
                context={"case_id": case.case_id, "expected_summary": case.expected_summary},
            )
        ],
        llm_caller=caller,
    )


def evaluator_record(case: TextifySmokeCase, caller: str, response_payload: JsonObject) -> JsonObject:
    return {
        "case_id": case.case_id,
        "caller": caller,
        "expected_summary": case.expected_summary,
        "response": response_payload,
    }


def write_json(path: Path, payload: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
