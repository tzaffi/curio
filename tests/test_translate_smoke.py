import json
from pathlib import Path

import pytest

from curio.config import CurioConfig, PipelineConfig, TranslateConfig
from curio.llm_caller import (
    LlmOutput,
    LlmRequest,
    LlmResponse,
    LlmUsage,
    MeteredObject,
    OpenAiApiAuthConfig,
    ProviderName,
)
from curio.llm_caller.auth import SecretRef
from curio.translate import (
    Block,
    LlmSummary,
    TranslatedBlock,
    TranslationRequest,
    TranslationResponse,
)
from live_smoke_helpers import (
    ModelPricing,
    SmokeCase,
    SmokeHarnessError,
    api_equivalent_cost_usd,
    build_smoke_translation_service,
    evaluator_input_record,
    redacted_caller_summary,
    render_translation_text,
    select_codex_smoke_caller,
    usage_payload,
    write_smoke_artifacts,
)


class RecordingLlmClient:
    def __init__(self, response: LlmResponse) -> None:
        self.response = response
        self.requests: list[LlmRequest] = []

    def complete(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return self.response


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def make_usage(
    *,
    input_tokens: int | None = 100,
    cached_input_tokens: int | None = 20,
    output_tokens: int | None = 30,
) -> LlmUsage:
    return LlmUsage(
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=5,
        total_tokens=130,
        metered_objects=[MeteredObject(name="request", quantity=1, unit="count")],
        started_at="2026-04-26T10:00:00Z",
        completed_at="2026-04-26T10:00:02Z",
        wall_seconds=2,
        thinking_seconds=None,
    )


def make_request() -> TranslationRequest:
    return TranslationRequest(
        request_id="smoke-test",
        blocks=[
            Block(block_id=1, name="first", source_language_hint="ja", text="こんにちは"),
            Block(block_id=2, name="second", source_language_hint="en", text="Already English."),
        ],
        llm_caller="translator_codex_gpt_54_mini",
    )


def make_response() -> TranslationResponse:
    return TranslationResponse(
        request_id="smoke-test",
        blocks=[
            TranslatedBlock(
                block_id=1,
                name="first",
                detected_language="ja",
                english_confidence_estimate=0.01,
                translation_required=True,
                translated_text="Hello.",
                warnings=["ambiguous greeting"],
            ),
            TranslatedBlock(
                block_id=2,
                name="second",
                detected_language="en",
                english_confidence_estimate=0.99,
                translation_required=False,
                translated_text=None,
            ),
        ],
        llm=LlmSummary(provider="codex_cli", model="gpt-5.4-mini", usage=make_usage()),
        warnings=["request warning"],
    )


def make_case() -> SmokeCase:
    return SmokeCase(
        case_id="C-JA-01",
        source_text="こんにちは",
        expected_translation_intent="Translate the Japanese greeting.",
        preservation_requirements=("greeting meaning",),
    )


def make_pricing() -> ModelPricing:
    return ModelPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0.75,
        cached_input_price_per_million=0.075,
        output_price_per_million=4.5,
    )


def test_select_codex_smoke_caller_uses_configured_default_and_explicit_override() -> None:
    config_path = repo_root() / "config.example.codex_cli.json"

    config, caller_config = select_codex_smoke_caller(config_path)
    _, explicit_config = select_codex_smoke_caller(config_path, "translator_codex_gpt_55")

    assert isinstance(config, CurioConfig)
    assert caller_config.name == "translator_codex_gpt_54_mini"
    assert caller_config.provider == ProviderName.CODEX_CLI
    assert explicit_config.name == "translator_codex_gpt_55"


def test_select_codex_smoke_caller_reports_config_and_provider_errors(tmp_path: Path) -> None:
    with pytest.raises(SmokeHarnessError, match="Missing config file"):
        select_codex_smoke_caller(tmp_path / "missing.json")

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "pipeline": {
                    "downloads_dir": "downloads",
                    "artifact_root": None,
                },
                "llm_callers": {
                    "translator_openai": {
                        "provider": "openai_api",
                        "model": "gpt-5.4-mini",
                        "timeout_seconds": 300,
                        "auth": {
                            "provider": "openai_api",
                            "api_key_ref": {
                                "backend": "keyring",
                                "service": "curio/openai-api",
                                "account": "default-api-key",
                                "label": "OpenAI API key",
                            },
                            "organization": None,
                            "project": None,
                        },
                        "responses": {
                            "temperature": 0,
                            "reasoning_effort": "low",
                            "max_output_tokens": None,
                            "text_verbosity": "low",
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SmokeHarnessError, match="translate.llm_caller"):
        select_codex_smoke_caller(config_path)
    with pytest.raises(SmokeHarnessError, match="must use codex_cli"):
        select_codex_smoke_caller(config_path, "translator_openai")


def test_build_smoke_translation_service_passes_prompt_config_to_service() -> None:
    _, caller_config = select_codex_smoke_caller(repo_root() / "config.example.codex_cli.json")
    llm_response = LlmResponse(
        request_id="smoke-test",
        status="succeeded",
        provider="codex_cli",
        model="gpt-5.4-mini",
        output=LlmOutput(
            value={
                "request_id": "smoke-test",
                "blocks": [
                    {
                        "block_id": 1,
                        "name": "first",
                        "detected_language": "ja",
                        "english_confidence_estimate": 0.01,
                        "translation_required": True,
                        "translated_text": "Hello.",
                        "warnings": [],
                    },
                    {
                        "block_id": 2,
                        "name": "second",
                        "detected_language": "en",
                        "english_confidence_estimate": 0.99,
                        "translation_required": False,
                        "translated_text": None,
                        "warnings": [],
                    },
                ],
            }
        ),
        usage=make_usage(),
    )
    client = RecordingLlmClient(llm_response)

    service = build_smoke_translation_service(client, caller_config)
    response = service.translate(make_request())

    assert service.prompt_config == caller_config.prompt_config
    assert service.pricing_config == caller_config.pricing_config
    assert response.blocks[0].translated_text == "Hello."
    assert response.llm.cost_estimate is not None
    assert response.llm.cost_estimate.amount == pytest.approx(0.0002115)
    assert client.requests[0].metadata["llm_caller"] == "translator_codex_gpt_54_mini"


def test_render_translation_text_uses_translations_and_original_english_blocks() -> None:
    assert render_translation_text(make_request(), make_response()) == "Hello.\n\nAlready English."


def test_api_equivalent_cost_and_usage_payload_handle_missing_token_counts() -> None:
    pricing = make_pricing()
    usage = make_usage(input_tokens=None, cached_input_tokens=None, output_tokens=None)

    assert api_equivalent_cost_usd(make_usage(), pricing) == pytest.approx(0.0002115)
    assert api_equivalent_cost_usd(usage, pricing) is None
    assert usage_payload(make_usage(), pricing) == {
        "input_tokens": 100,
        "cached_input_tokens": 20,
        "output_tokens": 30,
        "reasoning_tokens": 5,
        "currency": "USD",
        "basis": "api_equivalent",
        "input_price_per_million": 0.75,
        "cached_input_price_per_million": 0.075,
        "output_price_per_million": 4.5,
        "api_equivalent_cost_usd": pytest.approx(0.0002115),
    }


def test_smoke_config_models_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="case_id"):
        SmokeCase(case_id="", source_text="x", expected_translation_intent="x", preservation_requirements=())
    with pytest.raises(ValueError, match="source_text"):
        SmokeCase(case_id="case", source_text="", expected_translation_intent="x", preservation_requirements=())
    with pytest.raises(ValueError, match="expected_translation_intent"):
        SmokeCase(case_id="case", source_text="x", expected_translation_intent="", preservation_requirements=())
    with pytest.raises(ValueError, match="preservation requirement"):
        SmokeCase(case_id="case", source_text="x", expected_translation_intent="x", preservation_requirements=("",))
    with pytest.raises(ValueError, match="input_price_per_million"):
        ModelPricing(
            currency="USD",
            basis="api_equivalent",
            input_price_per_million=-1,
            cached_input_price_per_million=0,
            output_price_per_million=0,
        )


def test_redacted_caller_summary_includes_no_secret_values() -> None:
    _, caller_config = select_codex_smoke_caller(repo_root() / "config.example.codex_cli.json")
    openai_config = CurioConfig(
        llm_callers={
            "translator_openai": caller_config.__class__(
                name="translator_openai",
                provider=ProviderName.OPENAI_API,
                model="gpt-5.4-mini",
                auth_config=OpenAiApiAuthConfig(
                    api_key_ref=SecretRef(
                        backend="keyring",
                        service="curio/openai-api",
                        account="default-api-key",
                        label="OpenAI API key",
                    )
                ),
                timeout_seconds=300,
            )
        },
        pipeline_config=PipelineConfig(downloads_dir=repo_root() / "downloads"),
        translate_config=TranslateConfig(llm_caller="translator_openai"),
    ).llm_caller_config("translator_openai")

    codex_summary = redacted_caller_summary(caller_config)
    openai_summary = redacted_caller_summary(openai_config)

    assert codex_summary["exec"] == {
        "executable": "codex",
        "sandbox": "read-only",
        "color": "never",
        "ephemeral": True,
        "json_events": True,
        "skip_git_repo_check": True,
        "ignore_user_config": False,
        "model_reasoning_effort": "low",
        "model_verbosity": "low",
        "extra_config": [],
    }
    assert "auth" not in codex_summary
    assert "auth" not in openai_summary


def test_evaluator_input_record_and_artifact_retention(tmp_path: Path) -> None:
    _, caller_config = select_codex_smoke_caller(repo_root() / "config.example.codex_cli.json")
    request = make_request()
    response = make_response()
    case = make_case()

    record = evaluator_input_record(
        case=case,
        caller_config=caller_config,
        request=request,
        response=response,
        run_root=tmp_path,
        pricing=make_pricing(),
    )
    written_record = write_smoke_artifacts(
        run_root=tmp_path,
        case=case,
        caller_config=caller_config,
        request=request,
        response=response,
        pricing=make_pricing(),
        stderr="warning: redacted",
    )

    assert record["response_path"] == "runs/C-JA-01/translator_codex_gpt_54_mini/response.json"
    assert record["response_warnings"] == ["request warning", "ambiguous greeting"]
    assert record["translated_text"] == "Hello.\n\nAlready English."
    assert record["usage"]["api_equivalent_cost_usd"] == pytest.approx(0.0002115)
    assert written_record == record
    assert (tmp_path / "cases" / "C-JA-01" / "source.txt").read_text(encoding="utf-8") == "こんにちは"
    assert "Translate the Japanese greeting." in (
        tmp_path / "cases" / "C-JA-01" / "expected.md"
    ).read_text(encoding="utf-8")
    assert json.loads(
        (tmp_path / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini" / "request.json").read_text(
            encoding="utf-8"
        )
    )["request_id"] == "smoke-test"
    assert json.loads(
        (tmp_path / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini" / "response.json").read_text(
            encoding="utf-8"
        )
    )["warnings"] == ["request warning"]
    assert (tmp_path / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini" / "translated.txt").read_text(
        encoding="utf-8"
    ) == "Hello.\n\nAlready English."
    assert json.loads(
        (tmp_path / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini" / "usage.json").read_text(encoding="utf-8")
    )["api_equivalent_cost_usd"] == pytest.approx(0.0002115)
    assert (tmp_path / "runs" / "C-JA-01" / "translator_codex_gpt_54_mini" / "stderr.txt").read_text(
        encoding="utf-8"
    ) == "warning: redacted"
    evaluator_lines = (tmp_path / "evaluation" / "evaluator-input.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(evaluator_lines) == 1
    assert json.loads(evaluator_lines[0])["case_id"] == "C-JA-01"
