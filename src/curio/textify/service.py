from dataclasses import dataclass

from curio.config import LlmCallerPromptConfig
from curio.llm_caller import (
    LlmClient,
    LlmPricing,
    LlmResponse,
    estimate_llm_cost,
)
from curio.textify.adapter import build_textify_llm_request
from curio.textify.media import (
    effective_mime_type,
    is_deterministic_text_media,
    is_provider_supported_media,
    source_sha256,
)
from curio.textify.models import (
    TextifiedSource,
    TextifyLlmSummary,
    TextifyRequest,
    TextifyRequestError,
    TextifyResponse,
    TextifySource,
    TextifyStatus,
)
from curio.textify.validation import textified_source_from_llm_response


@dataclass(frozen=True, slots=True)
class TextifyService:
    llm_client: LlmClient | None = None
    prompt_config: LlmCallerPromptConfig | None = None
    pricing_config: LlmPricing | None = None

    def textify(self, request: TextifyRequest) -> TextifyResponse:
        source = request.source
        skipped = _deterministic_skip_source(source)
        if skipped is not None:
            return TextifyResponse(request_id=request.request_id, source=skipped)
        unsupported = _unsupported_source(source)
        if unsupported is not None:
            return TextifyResponse(request_id=request.request_id, source=unsupported)
        if self.llm_client is None:
            raise TextifyRequestError("llm_client is required for non-text media")
        llm_response = self.llm_client.complete(build_textify_llm_request(request, source, self.prompt_config))
        textified_source = textified_source_from_llm_response(request, source, llm_response)
        return TextifyResponse(
            request_id=request.request_id,
            source=textified_source,
            llm=_summarize_llm_response(llm_response, self.pricing_config),
            warnings=llm_response.warnings,
        )


def _deterministic_skip_source(source: TextifySource) -> TextifiedSource | None:
    if source.context.get("evidence_text"):
        return _skipped_source(source, "source already has deterministic evidence_text")
    if not is_deterministic_text_media(source):
        return None
    return _skipped_source(source, "source is deterministic text media")


def _skipped_source(source: TextifySource, warning: str) -> TextifiedSource:
    return TextifiedSource(
        name=source.name,
        input_mime_type=effective_mime_type(source),
        source_sha256=source_sha256(source),
        textification_required=False,
        status=TextifyStatus.SKIPPED_TEXT_MEDIA,
        warnings=[warning],
    )


def _unsupported_source(source: TextifySource) -> TextifiedSource | None:
    if is_provider_supported_media(source):
        return None
    return TextifiedSource(
        name=source.name,
        input_mime_type=effective_mime_type(source),
        source_sha256=source_sha256(source),
        textification_required=True,
        status=TextifyStatus.UNSUPPORTED_MEDIA,
        warnings=["unsupported media type for textify v1"],
    )


def _summarize_llm_response(
    response: LlmResponse,
    pricing_config: LlmPricing | None,
) -> TextifyLlmSummary:
    usage = response.usage
    return TextifyLlmSummary(
        provider=response.provider,
        model=response.model,
        usage=usage,
        cost_estimate=estimate_llm_cost(usage, pricing_config),
    )
