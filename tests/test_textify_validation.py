from pathlib import Path

import pytest

import curio.textify.validation as validation
from curio.llm_caller import LlmOutput, LlmResponse, LlmStatus, LlmUsage, ProviderName
from curio.textify import (
    TextifyRequest,
    TextifyResponseError,
    TextifySource,
    file_sha256,
)
from curio.textify.validation import (
    MARKDOWN_CODE_FENCE_REPAIR_WARNING,
    textified_source_from_llm_response,
    validate_textified_model_source,
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


def make_source(path: Path, *, name: str = "scan.png") -> TextifySource:
    path.write_bytes(b"png")
    return TextifySource(
        name=name,
        path=str(path),
        mime_type="image/png",
        sha256=file_sha256(path),
        context={},
    )


def output_payload(
    *,
    request_id: str = "textify-test",
    name: str = "scan.png",
    status: str = "converted",
    suggested_files: list[object] | None = None,
) -> object:
    return {
        "request_id": request_id,
        "source": {
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
        },
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


def test_textified_source_from_llm_response_validates_and_assembles(tmp_path: Path) -> None:
    source = make_source(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", source=source)

    textified_source = textified_source_from_llm_response(request, source, make_response(output_payload()))

    assert textified_source.name == "scan.png"
    assert textified_source.source_sha256 == file_sha256(tmp_path / "scan.png")
    assert textified_source.suggested_files[0].text == "# Scan"


def test_textified_source_repairs_single_outer_markdown_code_fence(tmp_path: Path) -> None:
    source = make_source(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", source=source)

    textified_source = textified_source_from_llm_response(
        request,
        source,
        make_response(
            output_payload(
                suggested_files=[
                    {
                        "suggested_path": "scan.md",
                        "output_format": "markdown",
                        "text": "```markdown\n# Scan\n\nhello\n```",
                    }
                ],
            )
        ),
    )

    assert textified_source.suggested_files[0].text == "# Scan\n\nhello"
    assert textified_source.warnings == (MARKDOWN_CODE_FENCE_REPAIR_WARNING,)


def test_textify_code_fence_repair_rejects_empty_repaired_content(tmp_path: Path) -> None:
    source = make_source(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", source=source)

    with pytest.raises(TextifyResponseError, match="empty text"):
        textified_source_from_llm_response(
            request,
            source,
            make_response(
                output_payload(
                    suggested_files=[
                        {
                            "suggested_path": "scan.md",
                            "output_format": "markdown",
                            "text": "```\n\n```",
                        }
                    ],
                )
            ),
        )


def test_textify_code_fence_repair_ignores_non_outer_fences() -> None:
    assert validation._unwrap_single_outer_markdown_code_fence("```mark`down\n# Scan\n```") is None
    assert validation._unwrap_single_outer_markdown_code_fence("```markdown\n# Scan\n~~~") is None


def test_textify_validation_rejects_response_level_failures(tmp_path: Path) -> None:
    source = make_source(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", source=source)

    with pytest.raises(TextifyResponseError, match="request_id"):
        textified_source_from_llm_response(request, source, make_response(output_payload(), request_id="other"))

    with pytest.raises(TextifyResponseError, match="LLM output request_id"):
        textified_source_from_llm_response(request, source, make_response(output_payload(request_id="other")))

    with pytest.raises(TextifyResponseError, match="status must be succeeded"):
        textified_source_from_llm_response(request, source, make_response(output_payload(), status="failed"))

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
        textified_source_from_llm_response(request, source, response)


def test_textify_model_output_schema_validation_reports_bad_shapes() -> None:
    with pytest.raises(TextifyResponseError, match="schema validation"):
        validate_textify_model_output({"request_id": "textify-test", "source": {"name": "scan.png"}})


def test_textify_validation_rejects_source_identity_errors(tmp_path: Path) -> None:
    source = make_source(tmp_path / "scan.png")

    with pytest.raises(TextifyResponseError, match="name must match"):
        validate_textified_model_source(source, output_payload(name="wrong.png")["source"])


def test_textify_validation_rejects_status_and_file_errors(tmp_path: Path) -> None:
    source = make_source(tmp_path / "scan.png")

    with pytest.raises(TextifyResponseError, match="converted sources"):
        validate_textified_model_source(source, output_payload(suggested_files=[])["source"])

    with pytest.raises(TextifyResponseError, match="non-converted sources"):
        validate_textified_model_source(source, output_payload(status="no_text_found")["source"])

    validate_textified_model_source(
        source,
        output_payload(
            suggested_files=[
                {
                    "suggested_path": "scan.md",
                    "output_format": "markdown",
                    "text": "```\nhello\n```",
                }
            ]
        )["source"],
    )

    with pytest.raises(TextifyResponseError, match="safe relative path"):
        validate_textified_model_source(
            source,
            output_payload(
                suggested_files=[
                    {
                        "suggested_path": "/tmp/scan.md",
                        "output_format": "markdown",
                        "text": "```markdown\nhello\n```",
                    }
                ]
            )["source"],
        )

    code_source = TextifySource(
        name="code.png",
        path=source.path,
        mime_type="image/png",
        sha256=source.sha256,
        context={"artifact_kind": "code"},
    )
    validate_textified_model_source(
        code_source,
        output_payload(
            name="code.png",
            suggested_files=[
                {
                    "suggested_path": "code.py",
                    "output_format": "markdown",
                    "text": "```\nprint('ok')\n```",
                }
            ],
        )["source"],
    )

    validate_textified_model_source(
        source,
        output_payload(
            suggested_files=[
                {
                    "suggested_path": "script.py",
                    "output_format": "py",
                    "text": "print('ok')",
                }
            ]
        )["source"],
    )


def test_textify_validation_rejects_low_level_type_errors() -> None:
    with pytest.raises(TextifyResponseError, match="object"):
        validate_textified_model_source(
            TextifySource(path="/tmp/x.png", name="x", mime_type="image/png", sha256="abc"),
            1,
        )

    with pytest.raises(TextifyResponseError, match="page_count"):
        validate_textified_model_source(
            TextifySource(path="/tmp/x.png", name="x", mime_type="image/png", sha256="abc"),
            [
                {
                    "name": "x",
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": -1,
                    "warnings": [],
                }
            ][0],
        )

    with pytest.raises(TextifyResponseError, match="suggested_files must be a list"):
        validate_textified_model_source(
            TextifySource(path="/tmp/x.png", name="x", mime_type="image/png", sha256="abc"),
            [
                {
                    "name": "x",
                    "status": "converted",
                    "suggested_files": {},
                    "detected_languages": [],
                    "page_count": None,
                    "warnings": [],
                }
            ][0],
        )

    with pytest.raises(TextifyResponseError, match="warnings is required"):
        validate_textified_model_source(
            TextifySource(path="/tmp/x.png", name="x", mime_type="image/png", sha256="abc"),
            [
                {
                    "name": "x",
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": None,
                }
            ][0],
        )

    with pytest.raises(TextifyResponseError, match="name must be a string"):
        validate_textified_model_source(
            TextifySource(path="/tmp/x.png", name="x", mime_type="image/png", sha256="abc"),
            [
                {
                    "name": 1,
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": None,
                    "warnings": [],
                }
            ][0],
        )

    with pytest.raises(TextifyResponseError, match="name must not be empty"):
        validate_textified_model_source(
            TextifySource(path="/tmp/x.png", name="x", mime_type="image/png", sha256="abc"),
            [
                {
                    "name": " ",
                    "status": "no_text_found",
                    "suggested_files": [],
                    "detected_languages": [],
                    "page_count": None,
                    "warnings": [],
                }
            ][0],
        )
