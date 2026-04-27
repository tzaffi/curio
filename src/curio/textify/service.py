from collections.abc import Iterable
from dataclasses import dataclass

from curio.config import LlmCallerPromptConfig
from curio.llm_caller import (
    LlmClient,
    LlmPricing,
    LlmResponse,
    LlmUsage,
    MeteredObject,
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
    Artifact,
    TextifiedArtifact,
    TextifyLlmSummary,
    TextifyRequest,
    TextifyRequestError,
    TextifyResponse,
    TextifyStatus,
)
from curio.textify.validation import textified_artifacts_from_llm_response


@dataclass(frozen=True, slots=True)
class TextifyService:
    llm_client: LlmClient | None = None
    prompt_config: LlmCallerPromptConfig | None = None
    pricing_config: LlmPricing | None = None

    def textify(self, request: TextifyRequest) -> TextifyResponse:
        artifacts: list[TextifiedArtifact] = []
        llm_responses: list[LlmResponse] = []
        warnings: list[str] = []
        for artifact in request.artifacts:
            skipped = _deterministic_skip_artifact(artifact)
            if skipped is not None:
                artifacts.append(skipped)
                continue
            unsupported = _unsupported_artifact(artifact)
            if unsupported is not None:
                artifacts.append(unsupported)
                warnings.extend(unsupported.warnings)
                continue
            if self.llm_client is None:
                raise TextifyRequestError("llm_client is required for non-text media")
            llm_response = self.llm_client.complete(
                build_textify_llm_request(request, artifact, self.prompt_config)
            )
            llm_responses.append(llm_response)
            artifacts.extend(textified_artifacts_from_llm_response(request, artifact, llm_response))
            warnings.extend(llm_response.warnings)
        return TextifyResponse(
            request_id=request.request_id,
            artifacts=artifacts,
            llm=_summarize_llm_responses(llm_responses, self.pricing_config),
            warnings=_unique_warnings(warnings),
        )


def _deterministic_skip_artifact(artifact: Artifact) -> TextifiedArtifact | None:
    if artifact.context.get("evidence_text"):
        return _skipped_artifact(artifact, "artifact already has deterministic evidence_text")
    if not is_deterministic_text_media(artifact):
        return None
    return _skipped_artifact(artifact, "artifact is deterministic text media")


def _skipped_artifact(artifact: Artifact, warning: str) -> TextifiedArtifact:
    return TextifiedArtifact(
        artifact_id=artifact.artifact_id,
        name=artifact.name,
        input_mime_type=effective_mime_type(artifact),
        source_sha256=source_sha256(artifact),
        textification_required=False,
        status=TextifyStatus.SKIPPED_TEXT_MEDIA,
        warnings=[warning],
    )


def _unsupported_artifact(artifact: Artifact) -> TextifiedArtifact | None:
    if is_provider_supported_media(artifact):
        return None
    return TextifiedArtifact(
        artifact_id=artifact.artifact_id,
        name=artifact.name,
        input_mime_type=effective_mime_type(artifact),
        source_sha256=source_sha256(artifact),
        textification_required=True,
        status=TextifyStatus.UNSUPPORTED_MEDIA,
        warnings=["unsupported media type for textify v1"],
    )


def _summarize_llm_responses(
    responses: list[LlmResponse],
    pricing_config: LlmPricing | None,
) -> TextifyLlmSummary | None:
    if not responses:
        return None
    provider = responses[0].provider
    model = responses[0].model
    usage = _aggregate_usage([response.usage for response in responses])
    return TextifyLlmSummary(
        provider=provider,
        model=model,
        usage=usage,
        cost_estimate=estimate_llm_cost(usage, pricing_config),
    )


def _aggregate_usage(usages: list[LlmUsage]) -> LlmUsage:
    first = usages[0]
    last = usages[-1]
    return LlmUsage(
        input_tokens=_sum_optional_numbers(usage.input_tokens for usage in usages),
        cached_input_tokens=_sum_optional_numbers(usage.cached_input_tokens for usage in usages),
        output_tokens=_sum_optional_numbers(usage.output_tokens for usage in usages),
        reasoning_tokens=_sum_optional_numbers(usage.reasoning_tokens for usage in usages),
        total_tokens=_sum_optional_numbers(usage.total_tokens for usage in usages),
        metered_objects=_aggregate_metered_objects(usages),
        started_at=first.started_at,
        completed_at=last.completed_at,
        wall_seconds=sum(usage.wall_seconds for usage in usages),
        thinking_seconds=_sum_optional_numbers(usage.thinking_seconds for usage in usages),
    )


def _sum_optional_numbers(values: Iterable[float | int | None]) -> float | int | None:
    numbers = list(values)
    if any(number is None for number in numbers):
        return None
    return sum(numbers)


def _aggregate_metered_objects(usages: list[LlmUsage]) -> tuple[MeteredObject, ...]:
    totals: dict[tuple[str, str], float | int] = {}
    for usage in usages:
        for metered_object in usage.metered_objects:
            key = (metered_object.name, metered_object.unit)
            totals[key] = totals.get(key, 0) + metered_object.quantity
    return tuple(MeteredObject(name=name, unit=unit, quantity=quantity) for (name, unit), quantity in totals.items())


def _unique_warnings(warnings: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(warnings))
