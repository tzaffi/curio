from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast

from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai

from curio.llm_caller.auth import GoogleDocumentAiAuthConfig
from curio.llm_caller.local_files import (
    read_local_file_content_part,
    single_local_file_content_part,
)
from curio.llm_caller.models import (
    JsonObject,
    JsonValue,
    LlmCapability,
    LlmInvalidOutputError,
    LlmRejectedRequestError,
    LlmRequest,
    LlmResponse,
    LocalFileContentPart,
    MeteredObject,
    ProviderName,
)
from curio.llm_caller.providers import (
    ProviderCallTiming,
    ProviderClientBase,
    ProviderClientConfig,
    build_json_llm_response,
    build_provider_usage,
    measure_provider_call,
)

GOOGLE_DOCUMENT_AI_CAPABILITIES = (
    LlmCapability.FILE_INPUT,
    LlmCapability.IMAGE_INPUT,
    LlmCapability.PDF_INPUT,
    LlmCapability.DOCUMENT_TEXT_EXTRACTION,
    LlmCapability.OCR,
    LlmCapability.LAYOUT_EXTRACTION,
    LlmCapability.MARKDOWN_OUTPUT,
    LlmCapability.PLAIN_TEXT_OUTPUT,
    LlmCapability.SUGGESTED_FILE_OUTPUT,
    LlmCapability.RELATIVE_PATH_OUTPUT,
    LlmCapability.METERED_PAGE_USAGE,
)


@dataclass(frozen=True, slots=True)
class GoogleDocumentAiCallResult:
    payload: Mapping[str, JsonValue]
    timing: ProviderCallTiming

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(_require_mapping(self.payload, "payload")))


class GoogleDocumentAiTransport(Protocol):
    def process_document(
        self,
        file_part: LocalFileContentPart,
        *,
        auth_config: GoogleDocumentAiAuthConfig,
        timeout_seconds: int,
    ) -> GoogleDocumentAiCallResult: ...


class SdkGoogleDocumentAiTransport:  # pragma: no cover
    def process_document(
        self,
        file_part: LocalFileContentPart,
        *,
        auth_config: GoogleDocumentAiAuthConfig,
        timeout_seconds: int,
    ) -> GoogleDocumentAiCallResult:
        try:
            content = read_local_file_content_part(file_part, provider_name="google_document_ai")  # pragma: no cover
            endpoint = f"{auth_config.location}-documentai.googleapis.com"  # pragma: no cover
            client_options = ClientOptions(api_endpoint=endpoint)  # pragma: no cover
            client = documentai.DocumentProcessorServiceClient(  # pragma: no cover
                client_options=client_options
            )
            processor_name = _processor_name(auth_config)  # pragma: no cover
            raw_document = documentai.RawDocument(content=content, mime_type=file_part.mime_type)  # pragma: no cover
            process_request = documentai.ProcessRequest(  # pragma: no cover
                name=processor_name,
                raw_document=raw_document,
            )
            response, timing = measure_provider_call(  # pragma: no cover
                lambda: client.process_document(request=process_request, timeout=timeout_seconds)
            )
        except OSError as exc:  # pragma: no cover
            raise LlmRejectedRequestError("google_document_ai local file could not be read") from exc
        return GoogleDocumentAiCallResult(payload=_document_ai_response_to_mapping(response), timing=timing)  # pragma: no cover


class GoogleDocumentAiClient(ProviderClientBase):
    def __init__(
        self,
        *,
        transport: GoogleDocumentAiTransport,
        auth_config: GoogleDocumentAiAuthConfig,
        model: str,
        timeout_seconds: int,
    ) -> None:
        super().__init__(
            ProviderClientConfig(
                provider=ProviderName.GOOGLE_DOCUMENT_AI,
                capabilities=GOOGLE_DOCUMENT_AI_CAPABILITIES,
            )
        )
        self.transport = transport
        self.auth_config = auth_config
        self.model = _require_string(model, "model")
        self.timeout_seconds = _require_positive_int(timeout_seconds, "timeout_seconds")

    def complete_after_capability_check(self, request: LlmRequest) -> LlmResponse:
        file_part = single_local_file_content_part(request, provider_name="google_document_ai")
        call_result = self.transport.process_document(
            file_part,
            auth_config=self.auth_config,
            timeout_seconds=self.timeout_seconds,
        )
        output_value = build_google_document_ai_output_value(request, file_part, call_result.payload)
        usage = build_provider_usage(
            call_result.timing,
            metered_objects=_metered_pages(call_result.payload),
        )
        return build_json_llm_response(
            request,
            provider=ProviderName.GOOGLE_DOCUMENT_AI,
            model=self.model,
            output_value=output_value,
            usage=usage,
            warnings=_payload_warnings(call_result.payload),
        )


def build_google_document_ai_output_value(
    request: LlmRequest,
    file_part: LocalFileContentPart,
    payload: Mapping[str, JsonValue],
) -> JsonObject:
    text = _document_text(payload).strip()
    page_count = _page_count(payload)
    artifact_id = _metadata_positive_int(request.metadata.get("artifact_id"), "artifact_id")
    artifact_name = _metadata_string(request.metadata.get("artifact_name"), "artifact_name")
    if not text:
        status = "no_text_found"
        suggested_files: list[JsonObject] = []
    else:
        status = "converted"
        suggested_files = [
            {
                "suggested_path": _suggested_path(request, file_part),
                "output_format": _metadata_string(request.metadata.get("preferred_output_format"), "preferred_output_format")
                if request.metadata.get("preferred_output_format") in {"markdown", "txt"}
                else "markdown",
                "text": text,
            }
        ]
    return {
        "request_id": request.request_id,
        "artifacts": [
            {
                "artifact_id": artifact_id,
                "name": artifact_name,
                "status": status,
                "suggested_files": suggested_files,
                "detected_languages": _detected_languages(payload),
                "page_count": page_count,
                "warnings": _payload_warnings(payload),
            }
        ],
    }


def _metered_pages(payload: Mapping[str, JsonValue]) -> Sequence[MeteredObject]:
    page_count = _page_count(payload)
    if page_count is None:
        return ()
    return (MeteredObject(name="document_ai_pages", quantity=page_count, unit="page"),)


def _document_text(payload: Mapping[str, JsonValue]) -> str:
    document = _optional_mapping(payload.get("document"))
    text = payload.get("text")
    if text is None and document is not None:
        text = document.get("text")
    if text is None:
        return ""
    if not isinstance(text, str):
        raise LlmInvalidOutputError("text must be a string")
    return text


def _page_count(payload: Mapping[str, JsonValue]) -> int | None:
    pages = payload.get("pages")
    document = _optional_mapping(payload.get("document"))
    if pages is None and document is not None:
        pages = document.get("pages")
    if pages is None:
        return None
    if not isinstance(pages, list):
        raise LlmInvalidOutputError("pages must be a list")
    return len(pages)


def _detected_languages(payload: Mapping[str, JsonValue]) -> list[str]:
    languages = payload.get("detected_languages")
    if languages is None:
        return []
    if not isinstance(languages, list):
        raise LlmInvalidOutputError("detected_languages must be a list")
    return [_require_string(language, "language") for language in languages]


def _payload_warnings(payload: Mapping[str, JsonValue]) -> tuple[str, ...]:
    warnings = payload.get("warnings")
    if warnings is None:
        return ()
    if not isinstance(warnings, list):
        raise LlmInvalidOutputError("warnings must be a list")
    return tuple(_require_string(warning, "warning") for warning in warnings)


def _suggested_path(request: LlmRequest, file_part: LocalFileContentPart) -> str:
    suggested_path = request.metadata.get("suggested_path")
    if isinstance(suggested_path, str) and suggested_path.strip():
        return suggested_path
    name = file_part.name or "document"
    stem = name.rsplit(".", 1)[0] or "document"
    return f"{stem}.md"


def _metadata_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LlmRejectedRequestError(f"google_document_ai request metadata must include {field_name}")
    return value


def _metadata_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise LlmRejectedRequestError(f"google_document_ai request metadata must include positive {field_name}")
    return value


def _processor_name(auth_config: GoogleDocumentAiAuthConfig) -> str:  # pragma: no cover
    client_class = documentai.DocumentProcessorServiceClient
    if auth_config.processor_version is None:
        return client_class.processor_path(auth_config.project_id, auth_config.location, auth_config.processor_id)
    return client_class.processor_version_path(
        auth_config.project_id,
        auth_config.location,
        auth_config.processor_id,
        auth_config.processor_version,
    )


def _document_ai_response_to_mapping(response: object) -> Mapping[str, JsonValue]:  # pragma: no cover
    document = getattr(response, "document", response)
    model_dump = getattr(document, "model_dump", None)
    if callable(model_dump):
        return cast(Mapping[str, JsonValue], model_dump(mode="json"))
    to_dict = getattr(document, "to_dict", None)
    if callable(to_dict):
        return cast(Mapping[str, JsonValue], to_dict())
    return cast(Mapping[str, JsonValue], {"document": document})


def _require_mapping(value: object, field_name: str) -> Mapping[str, JsonValue]:
    if not isinstance(value, Mapping):
        raise LlmInvalidOutputError(f"{field_name} must be an object")
    return cast(Mapping[str, JsonValue], value)


def _optional_mapping(value: object) -> Mapping[str, JsonValue] | None:
    if value is None:
        return None
    return _require_mapping(value, "field")


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise LlmInvalidOutputError(f"{field_name} must be a string")
    if not value.strip():
        raise LlmInvalidOutputError(f"{field_name} must not be empty")
    return value


def _require_positive_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")
    return value
