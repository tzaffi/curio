from dataclasses import dataclass

from curio.llm_caller import LlmClient
from curio.translate.adapter import build_translation_llm_request
from curio.translate.models import (
    LlmSummary,
    TranslationRequest,
    TranslationResponse,
)
from curio.translate.validation import translated_blocks_from_llm_response


@dataclass(frozen=True, slots=True)
class TranslationService:
    llm_client: LlmClient

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        llm_request = build_translation_llm_request(request)
        llm_response = self.llm_client.complete(llm_request)
        blocks = translated_blocks_from_llm_response(request, llm_response)
        return TranslationResponse(
            request_id=request.request_id,
            blocks=blocks,
            llm=LlmSummary(
                provider=llm_response.provider,
                model=llm_response.model,
                usage=llm_response.usage,
            ),
            warnings=llm_response.warnings,
        )
