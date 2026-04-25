from dataclasses import dataclass

from curio.llm_caller import LlmClient
from curio.translate.models import (
    TranslationNotImplementedError,
    TranslationRequest,
    TranslationResponse,
)


@dataclass(frozen=True, slots=True)
class TranslationService:
    llm_client: LlmClient

    def translate(self, request: TranslationRequest) -> TranslationResponse:
        raise TranslationNotImplementedError("TranslationService behavior starts in the next checkpoint")
