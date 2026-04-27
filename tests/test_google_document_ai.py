from pathlib import Path

import pytest

from curio.llm_caller import (
    GOOGLE_DOCUMENT_AI_CAPABILITIES,
    GoogleDocumentAiAuthConfig,
    GoogleDocumentAiCallResult,
    GoogleDocumentAiClient,
    GoogleDocumentAiProcessorKind,
    JsonSchemaOutput,
    LlmCapability,
    LlmInvalidOutputError,
    LlmMessage,
    LlmRejectedRequestError,
    LlmRequest,
    LocalFileContentPart,
    MeteredObject,
    ProviderAuthConfigError,
    ProviderCallTiming,
    ProviderName,
    SdkGoogleDocumentAiTransport,
    TextContentPart,
    UnsupportedCapabilityError,
    build_google_document_ai_output_value,
)
from curio.textify import file_sha256


def make_timing() -> ProviderCallTiming:
    return ProviderCallTiming(
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:02Z",
        wall_seconds=2,
    )


def make_file_part(path: Path) -> LocalFileContentPart:
    path.write_bytes(b"fake image")
    return LocalFileContentPart(
        path=str(path),
        mime_type="image/png",
        sha256=file_sha256(path),
        name=path.name,
    )


def make_request(file_part: LocalFileContentPart) -> LlmRequest:
    return LlmRequest(
        request_id="textify-test",
        workflow="textify",
        instructions="Extract text.",
        input=[LlmMessage(role="user", content=[TextContentPart("see file"), file_part])],
        output=JsonSchemaOutput(name="curio_textify_model_output", schema={"type": "object"}),
        required_capabilities=[LlmCapability.FILE_INPUT, LlmCapability.METERED_PAGE_USAGE],
        metadata={
            "artifact_id": 1,
            "artifact_name": file_part.name or "scan.png",
            "preferred_output_format": "markdown",
            "suggested_path": "scan.md",
        },
    )


class FakeGoogleDocumentAiTransport:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls: list[tuple[LocalFileContentPart, GoogleDocumentAiAuthConfig, int]] = []

    def process_document(
        self,
        file_part: LocalFileContentPart,
        *,
        auth_config: GoogleDocumentAiAuthConfig,
        timeout_seconds: int,
    ) -> GoogleDocumentAiCallResult:
        self.calls.append((file_part, auth_config, timeout_seconds))
        return GoogleDocumentAiCallResult(payload=self.payload, timing=make_timing())


def test_google_document_ai_auth_config_round_trips() -> None:
    config = GoogleDocumentAiAuthConfig(
        project_id="proj",
        location="us",
        processor_id="processor",
        processor_version="v1",
        processor_kind="layout_parser",
    )

    assert config.provider == ProviderName.GOOGLE_DOCUMENT_AI
    assert config.processor_kind == GoogleDocumentAiProcessorKind.LAYOUT_PARSER
    assert GoogleDocumentAiAuthConfig.from_json(config.to_json()) == config

    payload = config.to_json()
    payload["provider"] = "codex_cli"
    with pytest.raises(ProviderAuthConfigError, match="provider must be google_document_ai"):
        GoogleDocumentAiAuthConfig.from_json(payload)


def test_google_document_ai_client_uses_fake_transport_and_page_usage(tmp_path: Path) -> None:
    file_part = make_file_part(tmp_path / "scan.png")
    transport = FakeGoogleDocumentAiTransport(
        {
            "document": {"text": "Hello from OCR", "pages": [{"page": 1}, {"page": 2}]},
            "detected_languages": ["en"],
            "warnings": ["faint text"],
        }
    )
    auth_config = GoogleDocumentAiAuthConfig(project_id="proj", location="us", processor_id="processor")
    client = GoogleDocumentAiClient(
        transport=transport,
        auth_config=auth_config,
        model="document-ai-layout-parser",
        timeout_seconds=123,
    )

    response = client.complete(make_request(file_part))

    assert LlmCapability.METERED_PAGE_USAGE in GOOGLE_DOCUMENT_AI_CAPABILITIES
    assert transport.calls == [(file_part, auth_config, 123)]
    assert response.provider == ProviderName.GOOGLE_DOCUMENT_AI
    assert response.output is not None
    assert response.output.value["artifacts"][0]["suggested_files"][0]["text"] == "Hello from OCR"
    assert response.usage.metered_objects == (MeteredObject("document_ai_pages", 2, "page"),)
    assert response.warnings == ("faint text",)

    no_pages_transport = FakeGoogleDocumentAiTransport({"text": "hello"})
    no_pages_client = GoogleDocumentAiClient(
        transport=no_pages_transport,
        auth_config=auth_config,
        model="document-ai-layout-parser",
        timeout_seconds=123,
    )
    assert no_pages_client.complete(make_request(file_part)).usage.metered_objects == ()


def test_google_document_ai_sdk_transport_validates_local_file_integrity_before_upload(tmp_path: Path) -> None:
    file_part = make_file_part(tmp_path / "scan.png")
    auth_config = GoogleDocumentAiAuthConfig(project_id="proj", location="us", processor_id="processor")
    transport = SdkGoogleDocumentAiTransport()

    bad_sha = LocalFileContentPart(
        path=file_part.path,
        mime_type=file_part.mime_type,
        sha256="bad-sha",
        name=file_part.name,
    )
    with pytest.raises(LlmRejectedRequestError, match="sha256"):
        transport.process_document(bad_sha, auth_config=auth_config, timeout_seconds=1)

    missing = LocalFileContentPart(
        path=str((tmp_path / "missing.png").resolve()),
        mime_type=file_part.mime_type,
        sha256=file_part.sha256,
        name=file_part.name,
    )
    with pytest.raises(LlmRejectedRequestError, match="not readable"):
        transport.process_document(missing, auth_config=auth_config, timeout_seconds=1)


def test_google_document_ai_output_handles_empty_text_and_top_level_pages(tmp_path: Path) -> None:
    file_part = make_file_part(tmp_path / "scan.png")
    request = make_request(file_part)

    output = build_google_document_ai_output_value(
        request,
        file_part,
        {"text": " ", "pages": [{}]},
    )

    assert output["artifacts"][0]["status"] == "no_text_found"
    assert output["artifacts"][0]["suggested_files"] == []
    assert output["artifacts"][0]["page_count"] == 1

    blank = build_google_document_ai_output_value(request, file_part, {})
    assert blank["artifacts"][0]["status"] == "no_text_found"

    fallback_request = LlmRequest(
        request_id=request.request_id,
        workflow=request.workflow,
        instructions=request.instructions,
        input=request.input,
        output=request.output,
        required_capabilities=request.required_capabilities,
        metadata={
            "artifact_id": 1,
            "artifact_name": "scan.png",
            "preferred_output_format": "other",
        },
    )
    unnamed_part = LocalFileContentPart(path=file_part.path, mime_type=file_part.mime_type, sha256=file_part.sha256)
    fallback = build_google_document_ai_output_value(fallback_request, unnamed_part, {"text": "hello"})
    assert fallback["artifacts"][0]["suggested_files"][0]["suggested_path"] == "document.md"
    assert fallback["artifacts"][0]["suggested_files"][0]["output_format"] == "markdown"


def test_google_document_ai_rejects_invalid_transport_payloads(tmp_path: Path) -> None:
    file_part = make_file_part(tmp_path / "scan.png")

    with pytest.raises(LlmInvalidOutputError, match="payload"):
        GoogleDocumentAiCallResult(payload=[], timing=make_timing())

    with pytest.raises(LlmInvalidOutputError, match="pages"):
        build_google_document_ai_output_value(make_request(file_part), file_part, {"text": "hello", "pages": "bad"})

    with pytest.raises(LlmInvalidOutputError, match="detected_languages"):
        build_google_document_ai_output_value(
            make_request(file_part),
            file_part,
            {"text": "hello", "detected_languages": "bad"},
        )

    with pytest.raises(LlmInvalidOutputError, match="warnings"):
        build_google_document_ai_output_value(make_request(file_part), file_part, {"text": "hello", "warnings": "bad"})

    with pytest.raises(LlmInvalidOutputError, match="text"):
        build_google_document_ai_output_value(make_request(file_part), file_part, {"text": 1})

    with pytest.raises(LlmInvalidOutputError, match="language"):
        build_google_document_ai_output_value(make_request(file_part), file_part, {"text": "hello", "detected_languages": [1]})

    with pytest.raises(LlmInvalidOutputError, match="warning"):
        build_google_document_ai_output_value(make_request(file_part), file_part, {"text": "hello", "warnings": [" "]})


def test_google_document_ai_rejects_bad_request_metadata_and_file_count(tmp_path: Path) -> None:
    file_part = make_file_part(tmp_path / "scan.png")
    request = make_request(file_part)
    bad_metadata = LlmRequest(
        request_id=request.request_id,
        workflow=request.workflow,
        instructions=request.instructions,
        input=request.input,
        output=request.output,
        required_capabilities=request.required_capabilities,
        metadata={},
    )

    with pytest.raises(LlmRejectedRequestError, match="artifact_id"):
        build_google_document_ai_output_value(bad_metadata, file_part, {"text": "hello"})

    bad_name_metadata = LlmRequest(
        request_id=request.request_id,
        workflow=request.workflow,
        instructions=request.instructions,
        input=request.input,
        output=request.output,
        required_capabilities=request.required_capabilities,
        metadata={"artifact_id": 1, "artifact_name": ""},
    )
    with pytest.raises(LlmRejectedRequestError, match="artifact_name"):
        build_google_document_ai_output_value(bad_name_metadata, file_part, {"text": "hello"})

    no_file_request = LlmRequest(
        request_id="textify-test",
        workflow="textify",
        instructions="Extract",
        input=[LlmMessage(role="user", content=[TextContentPart("no file")])],
        output=JsonSchemaOutput(name="output", schema={}),
        required_capabilities=[],
        metadata={},
    )
    client = GoogleDocumentAiClient(
        transport=FakeGoogleDocumentAiTransport({"text": "hello"}),
        auth_config=GoogleDocumentAiAuthConfig("proj", "us", "processor"),
        model="document-ai-layout-parser",
        timeout_seconds=1,
    )

    with pytest.raises(LlmRejectedRequestError, match="exactly one local file"):
        client.complete_after_capability_check(no_file_request)

    with pytest.raises(ValueError, match="timeout_seconds"):
        GoogleDocumentAiClient(
            transport=FakeGoogleDocumentAiTransport({"text": "hello"}),
            auth_config=GoogleDocumentAiAuthConfig("proj", "us", "processor"),
            model="document-ai-layout-parser",
            timeout_seconds=0,
        )


def test_google_document_ai_capability_check_runs_before_transport(tmp_path: Path) -> None:
    file_part = make_file_part(tmp_path / "scan.png")
    transport = FakeGoogleDocumentAiTransport({"text": "hello"})
    client = GoogleDocumentAiClient(
        transport=transport,
        auth_config=GoogleDocumentAiAuthConfig("proj", "us", "processor"),
        model="document-ai-layout-parser",
        timeout_seconds=1,
    )
    request = make_request(file_part)
    request = LlmRequest(
        request_id=request.request_id,
        workflow=request.workflow,
        instructions=request.instructions,
        input=request.input,
        output=request.output,
        required_capabilities=[LlmCapability.SUBPROCESS],
        metadata=request.metadata,
    )

    with pytest.raises(UnsupportedCapabilityError, match="subprocess"):
        client.complete(request)
    assert transport.calls == []
