from pathlib import Path

import pytest

from curio.llm_caller import LlmOutput, LlmResponse, LlmStatus, LlmUsage, ProviderName
from curio.textify import Artifact, TextifyRequest, TextifyResponseError, file_sha256
from curio.textify.validation import (
    textified_artifacts_from_llm_response,
    validate_textified_model_artifacts,
    validate_textify_model_output,
)


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=1,
        cached_input_tokens=None,
        output_tokens=2,
        reasoning_tokens=None,
        total_tokens=3,
        metered_objects=[],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:01Z",
        wall_seconds=1,
        thinking_seconds=None,
    )


def make_artifact(path: Path, *, artifact_id: int = 1, name: str = "scan.png") -> Artifact:
    path.write_bytes(b"png")
    return Artifact(
        artifact_id=artifact_id,
        name=name,
        path=str(path),
        mime_type="image/png",
        sha256=file_sha256(path),
        context={},
    )


def output_payload(
    *,
    request_id: str = "textify-test",
    artifact_id: int = 1,
    name: str = "scan.png",
    status: str = "converted",
    suggested_files: list[object] | None = None,
) -> object:
    return {
        "request_id": request_id,
        "artifacts": [
            {
                "artifact_id": artifact_id,
                "name": name,
                "status": status,
                "suggested_files": [
                    {
                        "suggested_path": "scan.md",
                        "output_format": "markdown",
                        "text": "# Scan",
                    }
                ]
                if suggested_files is None
                else suggested_files,
                "detected_languages": ["en"],
                "page_count": None,
                "warnings": [],
            }
        ],
    }


def make_response(output: object, *, request_id: str = "textify-test", status: LlmStatus | str = "succeeded") -> LlmResponse:
    return LlmResponse(
        request_id=request_id,
        status=status,
        provider=ProviderName.CODEX_CLI,
        model="gpt-test",
        output=LlmOutput(value=output),
        usage=make_usage(),
    )


def test_textified_artifacts_from_llm_response_validates_and_assembles(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", artifacts=[artifact])

    artifacts = textified_artifacts_from_llm_response(request, artifact, make_response(output_payload()))

    assert artifacts[0].artifact_id == 1
    assert artifacts[0].source_sha256 == file_sha256(tmp_path / "scan.png")
    assert artifacts[0].suggested_files[0].text == "# Scan"


def test_textify_validation_rejects_response_level_failures(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", artifacts=[artifact])

    with pytest.raises(TextifyResponseError, match="request_id"):
        textified_artifacts_from_llm_response(request, artifact, make_response(output_payload(), request_id="other"))

    with pytest.raises(TextifyResponseError, match="LLM output request_id"):
        textified_artifacts_from_llm_response(request, artifact, make_response(output_payload(request_id="other")))

    with pytest.raises(TextifyResponseError, match="status must be succeeded"):
        textified_artifacts_from_llm_response(request, artifact, make_response(output_payload(), status="failed"))

    response = make_response(output_payload())
    response = LlmResponse(
        request_id=response.request_id,
        status=response.status,
        provider=response.provider,
        model=response.model,
        output=None,
        usage=response.usage,
    )
    with pytest.raises(TextifyResponseError, match="output is required"):
        textified_artifacts_from_llm_response(request, artifact, response)


def test_textify_model_output_schema_validation_reports_bad_shapes() -> None:
    with pytest.raises(TextifyResponseError, match="schema validation"):
        validate_textify_model_output({"request_id": "textify-test", "artifacts": [{"artifact_id": 1}]})


def test_textify_validation_rejects_artifact_identity_errors(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png")

    with pytest.raises(TextifyResponseError, match="duplicate"):
        validate_textified_model_artifacts([artifact], [output_payload()["artifacts"][0], output_payload()["artifacts"][0]])

    with pytest.raises(TextifyResponseError, match="missing"):
        validate_textified_model_artifacts([artifact], [])

    with pytest.raises(TextifyResponseError, match="unexpected"):
        validate_textified_model_artifacts([], [output_payload(artifact_id=2)["artifacts"][0]])

    second = make_artifact(tmp_path / "other.png", artifact_id=2, name="other.png")
    with pytest.raises(TextifyResponseError, match="order"):
        validate_textified_model_artifacts(
            [artifact, second],
            [output_payload(artifact_id=2, name="other.png")["artifacts"][0], output_payload()["artifacts"][0]],
        )

    with pytest.raises(TextifyResponseError, match="name must match"):
        validate_textified_model_artifacts([artifact], [output_payload(name="wrong.png")["artifacts"][0]])


def test_textify_validation_rejects_status_and_file_errors(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png")

    with pytest.raises(TextifyResponseError, match="converted artifacts"):
        validate_textified_model_artifacts([artifact], [output_payload(suggested_files=[])["artifacts"][0]])

    with pytest.raises(TextifyResponseError, match="non-converted artifacts"):
        validate_textified_model_artifacts([artifact], [output_payload(status="no_text_found")["artifacts"][0]])

    with pytest.raises(TextifyResponseError, match="code fence"):
        validate_textified_model_artifacts(
            [artifact],
            [
                output_payload(
                    suggested_files=[
                        {
                            "suggested_path": "scan.md",
                            "output_format": "markdown",
                            "text": "```\nhello\n```",
                        }
                    ]
                )["artifacts"][0]
            ],
        )

    code_artifact = Artifact(
        artifact_id=1,
        name="code.png",
        path=artifact.path,
        mime_type="image/png",
        sha256=artifact.sha256,
        context={"artifact_kind": "code"},
    )
    validate_textified_model_artifacts(
        [code_artifact],
        [
            output_payload(
                name="code.png",
                suggested_files=[
                    {
                        "suggested_path": "code.py",
                    "output_format": "markdown",
                    "text": "```\nprint('ok')\n```",
                    }
                ],
            )["artifacts"][0]
        ],
    )

    validate_textified_model_artifacts(
        [artifact],
        [
            output_payload(
                suggested_files=[
                    {
                        "suggested_path": "script.py",
                        "output_format": "py",
                        "text": "print('ok')",
                    }
                ]
            )["artifacts"][0]
        ],
    )


def test_textify_validation_rejects_low_level_type_errors() -> None:
    with pytest.raises(TextifyResponseError, match="object"):
        validate_textified_model_artifacts([], [1])

    with pytest.raises(TextifyResponseError, match="artifact_id"):
        validate_textified_model_artifacts([], [{"artifact_id": 0}])

    with pytest.raises(TextifyResponseError, match="page_count"):
        validate_textified_model_artifacts(
            [Artifact(artifact_id=1, name="x", path="/tmp/x.png", mime_type="image/png", sha256="abc")],
            [
                {
                    "artifact_id": 1,
                    "name": "x",
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": -1,
                    "warnings": [],
                }
            ],
        )

    with pytest.raises(TextifyResponseError, match="suggested_files must be a list"):
        validate_textified_model_artifacts(
            [Artifact(artifact_id=1, name="x", path="/tmp/x.png", mime_type="image/png", sha256="abc")],
            [
                {
                    "artifact_id": 1,
                    "name": "x",
                    "status": "converted",
                    "suggested_files": {},
                    "detected_languages": [],
                    "page_count": None,
                    "warnings": [],
                }
            ],
        )

    with pytest.raises(TextifyResponseError, match="warnings is required"):
        validate_textified_model_artifacts(
            [Artifact(artifact_id=1, name="x", path="/tmp/x.png", mime_type="image/png", sha256="abc")],
            [
                {
                    "artifact_id": 1,
                    "name": "x",
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": None,
                }
            ],
        )

    with pytest.raises(TextifyResponseError, match="name must be a string"):
        validate_textified_model_artifacts(
            [Artifact(artifact_id=1, name="x", path="/tmp/x.png", mime_type="image/png", sha256="abc")],
            [
                {
                    "artifact_id": 1,
                    "name": 1,
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": None,
                    "warnings": [],
                }
            ],
        )

    with pytest.raises(TextifyResponseError, match="name must not be empty"):
        validate_textified_model_artifacts(
            [Artifact(artifact_id=1, name="x", path="/tmp/x.png", mime_type="image/png", sha256="abc")],
            [
                {
                    "artifact_id": 1,
                    "name": " ",
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": None,
                    "warnings": [],
                }
            ],
        )
