from pathlib import Path
from typing import cast

import pytest

import curio.textify as textify
from curio.llm_caller import (
    LlmCostEstimate,
    LlmOutput,
    LlmPricing,
    LlmRequest,
    LlmResponse,
    LlmUsage,
    MeteredObject,
)
from curio.schemas import SchemaName, SchemaValidationError, validate_json
from curio.textify import (
    PreferredOutputFormat,
    SuggestedTextFile,
    TextifiedSource,
    TextifyLlmSummary,
    TextifyRequest,
    TextifyRequestError,
    TextifyResponse,
    TextifyResponseError,
    TextifyService,
    TextifySource,
    TextifyStatus,
    effective_mime_type,
    file_sha256,
    is_deterministic_text_media,
    is_probably_plaintext,
    is_provider_supported_media,
    normalize_mime_type,
    preferred_output_hint,
    source_sha256,
    validate_suggested_path,
)


def write_file(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def make_source(path: Path, *, mime_type: str | None = None) -> TextifySource:
    return TextifySource(
        name=path.name,
        path=str(path),
        mime_type=mime_type,
        sha256=file_sha256(path),
        source_language_hint=None,
        context={"artifact_kind": "image"},
    )


def make_usage() -> LlmUsage:
    return LlmUsage(
        input_tokens=100,
        cached_input_tokens=10,
        output_tokens=20,
        reasoning_tokens=None,
        total_tokens=120,
        metered_objects=[MeteredObject(name="document_ai_pages", quantity=2, unit="page")],
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:01Z",
        wall_seconds=1,
        thinking_seconds=None,
    )


def make_request(path: Path) -> TextifyRequest:
    return TextifyRequest(
        request_id="textify-test",
        preferred_output_format="auto",
        source=make_source(path, mime_type="image/png"),
        llm_caller="textifier_codex_gpt_54_mini",
    )


class RecordingLlmClient:
    def __init__(self, output_value: object, usage: LlmUsage | None = None) -> None:
        self.output_value = output_value
        self.usage = make_usage() if usage is None else usage
        self.requests: list[LlmRequest] = []

    def complete(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return LlmResponse(
            request_id=request.request_id,
            status="succeeded",
            provider="codex_cli",
            model="gpt-test",
            output=LlmOutput(value=self.output_value),
            usage=self.usage,
            warnings=["provider warning"],
        )


def converted_output(
    request_id: str = "textify-test",
    name: str = "scan.png",
    suggested_files: list[object] | None = None,
) -> object:
    return {
        "request_id": request_id,
        "source": {
            "name": name,
            "status": "converted",
            "suggested_files": [
                {
                    "suggested_path": "notes/scan.md",
                    "output_format": "markdown",
                    "text": "# Receipt\n\n合計 1200円",
                }
            ]
            if suggested_files is None
            else suggested_files,
            "detected_languages": ["ja"],
            "page_count": 1,
            "warnings": ["low contrast"],
        },
    }


def test_textify_root_exports_public_service_contracts() -> None:
    assert textify.__all__ == [
        "DEFAULT_TEXTIFY_OUTPUT_FORMAT",
        "TEXTIFY_REQUEST_VERSION",
        "TEXTIFY_RESPONSE_VERSION",
        "TextifySource",
        "PreferredOutputFormat",
        "SuggestedTextFile",
        "TextifiedSource",
        "TextifyError",
        "TextifyLlmSummary",
        "TextifyRequest",
        "TextifyRequestError",
        "TextifyResponse",
        "TextifyResponseError",
        "TextifyService",
        "TextifyStatus",
        "effective_mime_type",
        "file_sha256",
        "is_deterministic_text_media",
        "is_probably_plaintext",
        "is_provider_supported_media",
        "normalize_mime_type",
        "preferred_output_hint",
        "source_sha256",
        "validate_suggested_path",
    ]


def test_textify_request_and_response_serialize_to_schema_payload(tmp_path: Path) -> None:
    artifact_path = write_file(tmp_path / "scan.png", b"png bytes")
    request = make_request(artifact_path)

    request_payload = request.to_json()

    assert request.preferred_output_format == PreferredOutputFormat.AUTO
    assert request_payload["textify_request_version"] == "curio-textify-request.v1"
    validate_json(request_payload, SchemaName.TEXTIFY_REQUEST)
    assert TextifyRequest.from_json(request_payload) == request

    response = TextifyResponse(
        request_id="textify-test",
        source=TextifiedSource(
            name="scan.png",
            input_mime_type="image/png",
            source_sha256=file_sha256(artifact_path),
            textification_required=True,
            status="converted",
            suggested_files=[
                SuggestedTextFile(
                    suggested_path="notes/scan.md",
                    output_format="markdown",
                    text="# Receipt",
                )
            ],
            detected_languages=["ja"],
            page_count=1,
            warnings=["low contrast"],
        ),
        llm=TextifyLlmSummary(
            provider="codex_cli",
            model="gpt-test",
            usage=make_usage(),
            cost_estimate=LlmCostEstimate("USD", "api_equivalent", 0.01, 0, 0, 0, 10, "document_ai_pages", "page"),
        ),
        warnings=["provider warning"],
    )

    payload = response.to_json()

    assert payload["llm"]["cost_estimate"]["metered_price_per_thousand"] == 10
    validate_json(payload, SchemaName.TEXTIFY_RESPONSE)
    assert TextifyResponse.from_json(payload) == response


def test_textify_from_json_rejects_schema_invalid_payload(tmp_path: Path) -> None:
    payload = make_request(write_file(tmp_path / "scan.png", b"png")).to_json()
    payload["preferred_output_format"] = "docx"

    with pytest.raises(SchemaValidationError, match="textify_request"):
        TextifyRequest.from_json(payload)


def test_textify_model_invariants_reject_invalid_values(tmp_path: Path) -> None:
    with pytest.raises(TextifyRequestError, match="source path must be absolute"):
        TextifySource(path="relative.png", name="relative")

    with pytest.raises(TextifyRequestError, match="source name must not be empty"):
        TextifySource(path="/")

    with pytest.raises(TextifyResponseError, match="converted sources"):
        TextifiedSource(
            name="scan.png",
            input_mime_type="image/png",
            source_sha256="abc",
            textification_required=True,
            status="converted",
        )

    with pytest.raises(TextifyResponseError, match="non-converted sources"):
        TextifiedSource(
            name="scan.png",
            input_mime_type="image/png",
            source_sha256="abc",
            textification_required=True,
            status="unsupported_media",
            suggested_files=[SuggestedTextFile("scan.md", "markdown", "text")],
        )

    with pytest.raises(TextifyResponseError, match="safe relative path"):
        validate_suggested_path("/tmp/file.md")

    with pytest.raises(TextifyResponseError, match="forward slashes"):
        validate_suggested_path(r"dir\\file.md")

    with pytest.raises(TextifyResponseError, match="normalized and relative"):
        validate_suggested_path("../file.md")

    with pytest.raises(TextifyResponseError, match="drive root"):
        validate_suggested_path("C:/file.md")

    with pytest.raises(TextifyResponseError, match="must not be auto"):
        SuggestedTextFile("file.md", "auto", "text")


def test_media_helpers_classify_text_binary_and_supported_media(tmp_path: Path) -> None:
    text_path = write_file(tmp_path / "note.txt", b"\xef\xbb\xbfhello\n")
    log_path = write_file(tmp_path / "server.log", b"hello\n")
    empty_path = write_file(tmp_path / "empty.bin", b"")
    bom_only_path = write_file(tmp_path / "bom.txt", b"\xef\xbb\xbf")
    invalid_utf8_path = write_file(tmp_path / "bad.log", b"\xff\xff")
    binary_path = write_file(tmp_path / "blob.txt", b"hello\x00world")
    image_path = write_file(tmp_path / "photo.webp", b"fake")
    pdf_path = write_file(tmp_path / "paper.pdf", b"%PDF")

    text_source = make_source(text_path, mime_type=None)
    image_source = make_source(image_path, mime_type="IMAGE/WEBP; charset=binary")

    assert normalize_mime_type(" IMAGE/PNG ; charset=binary ") == "image/png"
    assert normalize_mime_type(" ") is None
    assert effective_mime_type(text_source) == "text/plain"
    assert file_sha256(text_path) == source_sha256(text_source)
    assert is_probably_plaintext(text_path) is True
    assert is_probably_plaintext(log_path) is True
    assert is_probably_plaintext(empty_path) is True
    assert is_probably_plaintext(bom_only_path) is True
    assert is_probably_plaintext(invalid_utf8_path) is False
    assert is_probably_plaintext(binary_path) is False
    assert is_probably_plaintext(tmp_path / "missing.txt") is False
    assert is_deterministic_text_media(text_source) is True
    assert is_provider_supported_media(image_source) is True
    assert is_provider_supported_media(make_source(pdf_path, mime_type=None)) is True
    assert preferred_output_hint(text_source, PreferredOutputFormat.AUTO) == "txt"
    assert preferred_output_hint(image_source, "markdown") == "markdown"
    assert is_deterministic_text_media(make_source(log_path, mime_type=None)) is True
    assert is_deterministic_text_media(make_source(text_path, mime_type="application/octet-stream")) is True


def test_textify_service_skips_text_without_llm(tmp_path: Path) -> None:
    text_source = make_source(write_file(tmp_path / "note.txt", b"hello"), mime_type="text/plain")
    request = TextifyRequest(request_id="textify-test", source=text_source)

    response = TextifyService().textify(request)

    assert response.llm is None
    assert response.source.status == TextifyStatus.SKIPPED_TEXT_MEDIA
    assert response.source.textification_required is False
    validate_json(response.to_json(), SchemaName.TEXTIFY_RESPONSE)


def test_textify_service_skips_existing_evidence_text_without_llm(tmp_path: Path) -> None:
    evidence_source = TextifySource(
        name="evidence.png",
        path=str(write_file(tmp_path / "evidence.png", b"png")),
        mime_type="image/png",
        sha256="abc",
        context={"evidence_text": "already extracted"},
    )
    request = TextifyRequest(request_id="textify-test", source=evidence_source)

    response = TextifyService().textify(request)

    assert response.llm is None
    assert response.source.status == TextifyStatus.SKIPPED_TEXT_MEDIA
    assert response.source.textification_required is False
    validate_json(response.to_json(), SchemaName.TEXTIFY_RESPONSE)


def test_textify_service_marks_unsupported_without_llm(tmp_path: Path) -> None:
    unsupported = make_source(write_file(tmp_path / "archive.zip", b"zip"), mime_type="application/zip")
    request = TextifyRequest(request_id="textify-test", source=unsupported)

    response = TextifyService().textify(request)

    assert response.llm is None
    assert response.source.status == TextifyStatus.UNSUPPORTED_MEDIA
    assert response.source.textification_required is True
    assert response.warnings == ()
    assert response.source.warnings == ("unsupported media type for textify v1",)
    validate_json(response.to_json(), SchemaName.TEXTIFY_RESPONSE)


def test_textify_service_converts_with_fake_client_and_cost(tmp_path: Path) -> None:
    artifact_path = write_file(tmp_path / "scan.png", b"png")
    request = make_request(artifact_path)
    client = RecordingLlmClient(converted_output(name="scan.png"))

    response = TextifyService(
        llm_client=client,
        pricing_config=LlmPricing("USD", "api_equivalent", 0.75, 0.075, 4.5),
    ).textify(request)

    assert len(client.requests) == 1
    assert client.requests[0].workflow == "textify"
    assert response.source.suggested_files[0].text == "# Receipt\n\n合計 1200円"
    assert response.llm is not None
    assert response.llm.cost_estimate == LlmCostEstimate("USD", "api_equivalent", 0.00016575, 0.75, 0.075, 4.5)
    assert response.warnings == ("provider warning",)


def test_textify_service_requires_client_for_supported_non_text(tmp_path: Path) -> None:
    request = make_request(write_file(tmp_path / "scan.png", b"png"))

    with pytest.raises(TextifyRequestError, match="llm_client is required"):
        TextifyService().textify(request)


def test_textify_service_allows_multiple_suggested_files_from_one_source(tmp_path: Path) -> None:
    source_path = write_file(tmp_path / "scripts.png", b"png")
    request = make_request(source_path)
    client = RecordingLlmClient(
        converted_output(
            name="scripts.png",
            suggested_files=[
                {"suggested_path": "scripts/setup.sh", "output_format": "txt", "text": "echo setup"},
                {"suggested_path": "scripts/run.sh", "output_format": "txt", "text": "echo run"},
            ],
        )
    )

    response = TextifyService(llm_client=client).textify(request)

    assert len(client.requests) == 1
    assert [suggested.suggested_path for suggested in response.source.suggested_files] == [
        "scripts/setup.sh",
        "scripts/run.sh",
    ]


def test_textify_nested_parsers_reject_invalid_shapes() -> None:
    with pytest.raises(ValueError, match="request_id must not be empty"):
        TextifyRequest(request_id="", source=TextifySource(path="/tmp/x.txt", name="x"))

    with pytest.raises(TextifyRequestError, match="source must be"):
        TextifyRequest(request_id="textify-test", source=cast(TextifySource, "bad source"))

    with pytest.raises(ValueError, match="textification_required must be a boolean"):
        TextifiedSource(
            name="scan.png",
            input_mime_type=None,
            source_sha256=None,
            textification_required=cast(bool, "yes"),
            status="skipped_text_media",
        )

    with pytest.raises(ValueError, match="page_count must be a non-negative number"):
        TextifiedSource(
            name="scan.png",
            input_mime_type=None,
            source_sha256=None,
            textification_required=False,
            status="skipped_text_media",
            page_count=-1,
        )

    with pytest.raises(ValueError, match="source must be an object"):
        TextifySource.from_json([])

    with pytest.raises(ValueError, match="suggested_files must be a list"):
        TextifiedSource.from_json(
            {
                "name": "scan.png",
                "input_mime_type": None,
                "source_sha256": None,
                "textification_required": True,
                "status": "converted",
                "suggested_files": {},
                "detected_languages": [],
                "page_count": None,
                "warnings": [],
            }
        )

    with pytest.raises(ValueError, match="warnings must be unique"):
        TextifyResponse(
            request_id="textify-test",
            source=TextifiedSource(
                name="scan.png",
                input_mime_type=None,
                source_sha256=None,
                textification_required=False,
                status="skipped_text_media",
            ),
            warnings=["same", "same"],
        )

    with pytest.raises(ValueError, match="path is required"):
        TextifySource.from_json(
            {
                "name": "scan",
                "mime_type": None,
                "sha256": None,
                "source_language_hint": None,
                "context": {},
            }
        )

    with pytest.raises(ValueError, match="suggested_path is required"):
        SuggestedTextFile.from_json({"output_format": "markdown", "text": "hello"})

    with pytest.raises(ValueError, match="language values must be unique"):
        TextifiedSource(
            name="scan.png",
            input_mime_type=None,
            source_sha256=None,
            textification_required=True,
            status="converted",
            suggested_files=[SuggestedTextFile("scan.md", "markdown", "hello")],
            detected_languages=["en", "en"],
        )

    with pytest.raises(TextifyResponseError, match="source must be"):
        TextifyResponse(request_id="textify-test", source=cast(TextifiedSource, "bad source"))

    with pytest.raises(ValueError, match="provider"):
        TextifyLlmSummary.from_json({"provider": 1, "model": None, "usage": make_usage().to_json(), "cost_estimate": None})

    with pytest.raises(SchemaValidationError, match="textify_response"):
        TextifyResponse.from_json(
            {
                "textify_response_version": "curio-textify-response.v1",
                "request_id": "textify-test",
                "source": TextifiedSource(
                    name="scan.png",
                    input_mime_type=None,
                    source_sha256=None,
                    textification_required=False,
                    status="skipped_text_media",
                ).to_json(),
                "llm": None,
                "warnings": [cast(str, 1)],
            }
        )
