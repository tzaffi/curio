import hashlib
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
from curio.textify import (
    SuggestedTextFile,
    TextifiedSource,
    TextifyLlmSummary,
    TextifyResponse,
)
from textify_smoke_helpers import (
    TEXTIFY_NOOP_SMOKE_CASE,
    TEXTIFY_SMOKE_CALLERS,
    TEXTIFY_SMOKE_CASES,
    TEXTIFY_SMOKE_FIXTURE_MANIFEST,
    TEXTIFY_SMOKE_FIXTURE_ROOT,
    ModelPricing,
    TextifySmokeCase,
    TextifySmokeHarnessError,
    api_equivalent_cost_usd,
    build_smoke_textify_service,
    build_textify_smoke_request,
    evaluator_input_record,
    fixture_metadata,
    redacted_caller_summary,
    render_textified_output,
    select_codex_textify_caller,
    usage_payload,
    write_textify_smoke_artifacts,
    write_textify_smoke_fixture,
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
        metered_objects=[MeteredObject(name="image", quantity=1, unit="count")],
        started_at="2026-04-27T10:00:00Z",
        completed_at="2026-04-27T10:00:03Z",
        wall_seconds=3,
        thinking_seconds=None,
    )


def make_pricing() -> ModelPricing:
    return ModelPricing(
        currency="USD",
        basis="api_equivalent",
        input_price_per_million=0.75,
        cached_input_price_per_million=0.075,
        output_price_per_million=4.5,
    )


def make_textify_response() -> TextifyResponse:
    return TextifyResponse(
        request_id="textify-smoke-C-IMG-TXT-01-textifier_codex_gpt_54_mini",
        source=TextifiedSource(
            name="plain-note.png",
            input_mime_type="image/png",
            source_sha256="abc",
            textification_required=True,
            status="converted",
            suggested_files=[
                SuggestedTextFile(
                    suggested_path="note.txt",
                    output_format="txt",
                    text="DEPLOY NOTE\nRUN UV SYNC",
                )
            ],
            detected_languages=["en"],
            warnings=["low confidence corner"],
        ),
        llm=TextifyLlmSummary(
            provider=ProviderName.CODEX_CLI,
            model="gpt-5.4-mini",
            usage=make_usage(),
        ),
        warnings=["provider warning"],
    )


def test_textify_smoke_case_matrix_is_reviewed_shape() -> None:
    assert TEXTIFY_SMOKE_CALLERS == (
        "textifier_codex_gpt_54_mini",
        "textifier_codex_gpt_53_codex",
        "textifier_codex_gpt_55",
    )
    case_ids = [case.case_id for case in TEXTIFY_SMOKE_CASES]
    assert case_ids[:9] == [
        "C-IMG-TXT-01",
        "C-IMG-CODE-01",
        "C-IMG-CODE-02",
        "C-IMG-MULTI-01",
        "C-IMG-POST-01",
        "C-PDF-DOC-01",
        "C-PDF-TABLE-01",
        "C-IMG-RECEIPT-01",
        "C-IMG-NO-TEXT-01",
    ]
    assert case_ids[9:] == [
        "R-IMG-DASH-01",
        "R-IMG-LLM-TABLE-01",
        "R-IMG-INFOGRAPHIC-01",
        "R-IMG-PAPER-PAGE-01",
        "R-IMG-CHARTS-01",
        "R-IMG-TERMINAL-01",
        "R-IMG-ASCII-DIAGRAM-01",
        "R-IMG-COMPARISON-TABLE-01",
        "R-IMG-NO-TEXT-REAL-01",
        "C-IMG-DIR-TREE-01",
        "R-PDF-PAPER-01",
        "R-HTML-ARXIV-01",
        "R-HTML-GITHUB-README-01",
        "R-JSON-XARTICLE-CODE-01",
        "R-ZIP-REPO-01",
    ]
    assert all(case.model_importance == 1 for case in TEXTIFY_SMOKE_CASES[:9])
    assert all(case.participates_in_model_ranking for case in TEXTIFY_SMOKE_CASES[:20])
    assert [case.model_importance for case in TEXTIFY_SMOKE_CASES[9:20]] == [9, 10, 10, 9, 8, 8, 8, 8, 5, 10, 10]
    assert all(not case.participates_in_model_ranking for case in TEXTIFY_SMOKE_CASES[20:])
    assert TEXTIFY_NOOP_SMOKE_CASE.case_id == "C-TEXT-NOOP-01"
    assert TEXTIFY_NOOP_SMOKE_CASE.model_importance == 1
    assert TEXTIFY_NOOP_SMOKE_CASE.expect_llm_call is False


def test_textify_real_fixture_manifest_matches_checked_in_files() -> None:
    payload = json.loads(TEXTIFY_SMOKE_FIXTURE_MANIFEST.read_text(encoding="utf-8"))

    assert payload["version"] == 1
    assert len(payload["cases"]) == 15
    for case in TEXTIFY_SMOKE_CASES[9:]:
        assert case.fixture_path is not None
        fixture_path = TEXTIFY_SMOKE_FIXTURE_ROOT / case.fixture_path
        assert fixture_path.exists()
        assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == case.fixture_sha256
        assert 1 <= case.model_importance <= 10
    composite = next(case for case in TEXTIFY_SMOKE_CASES if case.case_id == "C-IMG-DIR-TREE-01")
    assert composite.expected_suggested_paths == (
        "home/important/openclaw-rl.md",
        "home/important/agent-comparison.md",
        "home/trivial/claude-code-listing.log",
    )
    assert composite.model_importance == 10


def test_textify_smoke_config_selection_and_prompt_requirements() -> None:
    config_path = repo_root() / "config.example.codex_cli.json"

    config, caller_config = select_codex_textify_caller(config_path)
    _, explicit_config = select_codex_textify_caller(config_path, "textifier_codex_gpt_55")

    assert isinstance(config, CurioConfig)
    assert caller_config.name == "textifier_codex_gpt_54_mini"
    assert caller_config.provider == ProviderName.CODEX_CLI
    assert caller_config.prompt_config is not None
    assert caller_config.prompt_config.user is not None
    assert "{textify_request_json}" in caller_config.prompt_config.user
    assert explicit_config.name == "textifier_codex_gpt_55"


def test_textify_smoke_config_reports_errors(tmp_path: Path) -> None:
    with pytest.raises(TextifySmokeHarnessError, match="Missing config file"):
        select_codex_textify_caller(tmp_path / "missing.json")

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
    with pytest.raises(TextifySmokeHarnessError, match="textify.llm_caller"):
        select_codex_textify_caller(config_path)
    with pytest.raises(TextifySmokeHarnessError, match="must use codex_cli"):
        select_codex_textify_caller(config_path, "translator_openai")


def test_textify_smoke_models_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="case_id"):
        TextifySmokeCase(
            case_id="",
            input_mode="artifact_path",
            fixture_kind="png_text",
            filename="x.png",
            mime_type="image/png",
            preferred_output_format="txt",
            expected_output_format="txt",
            expected_suggested_paths=(),
            expected_textification_intent="x",
            ground_truth_text="x",
            preservation_requirements=(),
        )
    with pytest.raises(ValueError, match="expected suggested path"):
        TextifySmokeCase(
            case_id="case",
            input_mode="artifact_path",
            fixture_kind="png_text",
            filename="x.png",
            mime_type="image/png",
            preferred_output_format="txt",
            expected_output_format="txt",
            expected_suggested_paths=("",),
            expected_textification_intent="x",
            ground_truth_text="x",
            preservation_requirements=(),
        )
    with pytest.raises(ValueError, match="model_importance"):
        TextifySmokeCase(
            case_id="case",
            input_mode="artifact_path",
            fixture_kind="png_text",
            filename="x.png",
            mime_type="image/png",
            preferred_output_format="txt",
            expected_output_format="txt",
            expected_suggested_paths=(),
            expected_textification_intent="x",
            ground_truth_text="x",
            preservation_requirements=(),
            model_importance=11,
        )


def test_generated_fixtures_and_requests_include_metadata(tmp_path: Path) -> None:
    image_case = TEXTIFY_SMOKE_CASES[0]
    noop_case = TEXTIFY_NOOP_SMOKE_CASE
    checked_in_case = next(case for case in TEXTIFY_SMOKE_CASES if case.case_id == "C-IMG-DIR-TREE-01")

    image_source = write_textify_smoke_fixture(image_case, tmp_path)
    noop_source = write_textify_smoke_fixture(noop_case, tmp_path)
    checked_in_source = write_textify_smoke_fixture(checked_in_case, tmp_path)
    request = build_textify_smoke_request(image_case, TEXTIFY_SMOKE_CALLERS[0], image_source)

    assert request.llm_caller == "textifier_codex_gpt_54_mini"
    assert request.preferred_output_format == "txt"
    assert image_source.sha256 is not None
    assert Path(image_source.path).read_bytes().startswith(b"\x89PNG")
    assert Path(noop_source.path).suffix == ".txt"
    assert Path(noop_source.path).read_text(encoding="utf-8").startswith("ALREADY TEXT")
    assert Path(checked_in_source.path).read_bytes().startswith(b"\x89PNG")
    assert checked_in_source.sha256 == checked_in_case.fixture_sha256
    assert fixture_metadata(image_source)["sha256"] == image_source.sha256
    assert "Ground Truth Text" in (tmp_path / "cases" / image_case.case_id / "expected.md").read_text(
        encoding="utf-8"
    )


def test_generated_pdf_fixtures_are_pdf_files(tmp_path: Path) -> None:
    pdf_case = next(case for case in TEXTIFY_SMOKE_CASES if case.case_id == "C-PDF-DOC-01")

    source = write_textify_smoke_fixture(pdf_case, tmp_path)

    assert Path(source.path).read_bytes().startswith(b"%PDF-1.4")


def test_textify_smoke_service_passes_prompt_config_and_pricing(tmp_path: Path) -> None:
    _, caller_config = select_codex_textify_caller(repo_root() / "config.example.codex_cli.json")
    llm_response = LlmResponse(
        request_id="textify-smoke-C-IMG-TXT-01-textifier_codex_gpt_54_mini",
        status="succeeded",
        provider=ProviderName.CODEX_CLI,
        model="gpt-5.4-mini",
        output=LlmOutput(
            value={
                "request_id": "textify-smoke-C-IMG-TXT-01-textifier_codex_gpt_54_mini",
                "source": {
                    "name": "plain-note.png",
                    "status": "converted",
                    "suggested_files": [
                        {
                            "suggested_path": "note.txt",
                            "output_format": "txt",
                            "text": "DEPLOY NOTE",
                        }
                    ],
                    "detected_languages": ["en"],
                    "page_count": 1,
                    "warnings": [],
                },
            }
        ),
        usage=make_usage(),
    )
    client = RecordingLlmClient(llm_response)
    case = TEXTIFY_SMOKE_CASES[0]
    source = write_textify_smoke_fixture(case, tmp_path)
    request = build_textify_smoke_request(case, caller_config.name, source)

    service = build_smoke_textify_service(client, caller_config)
    response = service.textify(request)

    assert service.prompt_config == caller_config.prompt_config
    assert service.pricing_config == caller_config.pricing_config
    assert response.source.suggested_files[0].text == "DEPLOY NOTE"
    assert response.llm is not None
    assert response.llm.cost_estimate is not None
    assert client.requests[0].metadata["llm_caller"] == "textifier_codex_gpt_54_mini"


def test_usage_payload_and_rendered_output() -> None:
    pricing = make_pricing()
    usage = make_usage(input_tokens=None, cached_input_tokens=None, output_tokens=None)
    response = make_textify_response()

    assert api_equivalent_cost_usd(make_usage(), pricing) == pytest.approx(0.0002115)
    assert api_equivalent_cost_usd(usage, pricing) is None
    assert usage_payload(make_usage(), pricing)["api_equivalent_cost_usd"] == pytest.approx(0.0002115)
    assert usage_payload(make_usage(), pricing)["metered_objects"] == [
        {"name": "image", "quantity": 1, "unit": "count"}
    ]
    assert render_textified_output(response) == "DEPLOY NOTE\nRUN UV SYNC"


def test_redacted_caller_summary_includes_no_secret_values() -> None:
    _, caller_config = select_codex_textify_caller(repo_root() / "config.example.codex_cli.json")
    openai_config = CurioConfig(
        llm_callers={
            "textifier_openai": caller_config.__class__(
                name="textifier_openai",
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
        translate_config=TranslateConfig(llm_caller=None),
    ).llm_caller_config("textifier_openai")

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
    _, caller_config = select_codex_textify_caller(repo_root() / "config.example.codex_cli.json")
    case = TEXTIFY_SMOKE_CASES[0]
    source = write_textify_smoke_fixture(case, tmp_path)
    request = build_textify_smoke_request(case, caller_config.name, source)
    response = make_textify_response()

    record = evaluator_input_record(
        case=case,
        caller_config=caller_config,
        source=source,
        response=response,
        run_root=tmp_path,
        pricing=make_pricing(),
    )
    written_record = write_textify_smoke_artifacts(
        run_root=tmp_path,
        case=case,
        caller_config=caller_config,
        source=source,
        request=request,
        response=response,
        pricing=make_pricing(),
        stderr="warning: redacted",
    )

    assert record["response_path"] == "runs/C-IMG-TXT-01/textifier_codex_gpt_54_mini/response.json"
    assert record["response_warnings"] == ["provider warning", "low confidence corner"]
    assert record["rendered_textified_text"] == "DEPLOY NOTE\nRUN UV SYNC"
    assert record["usage"]["api_equivalent_cost_usd"] == pytest.approx(0.0002115)
    assert record["suggested_files"][0]["suggested_path"] == "note.txt"
    assert record["model_importance"] == 1
    assert record["participates_in_model_ranking"] is True
    assert record["expected_status"] == "converted"
    assert written_record == record
    assert json.loads(
        (tmp_path / "runs" / "C-IMG-TXT-01" / "textifier_codex_gpt_54_mini" / "request.json").read_text(
            encoding="utf-8"
        )
    )["request_id"] == request.request_id
    assert json.loads(
        (tmp_path / "runs" / "C-IMG-TXT-01" / "textifier_codex_gpt_54_mini" / "response.json").read_text(
            encoding="utf-8"
        )
    )["warnings"] == ["provider warning"]
    assert (tmp_path / "runs" / "C-IMG-TXT-01" / "textifier_codex_gpt_54_mini" / "textified.txt").read_text(
        encoding="utf-8"
    ) == "DEPLOY NOTE\nRUN UV SYNC"
    assert json.loads(
        (tmp_path / "runs" / "C-IMG-TXT-01" / "textifier_codex_gpt_54_mini" / "usage.json").read_text(
            encoding="utf-8"
        )
    )["api_equivalent_cost_usd"] == pytest.approx(0.0002115)
    assert (
        tmp_path / "runs" / "C-IMG-TXT-01" / "textifier_codex_gpt_54_mini" / "stderr.txt"
    ).read_text(encoding="utf-8") == "warning: redacted"
    evaluator_lines = (tmp_path / "evaluation" / "evaluator-input.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(evaluator_lines) == 1
    assert json.loads(evaluator_lines[0])["case_id"] == "C-IMG-TXT-01"


def test_artifact_retention_supports_coverage_only_cases_without_llm_usage(tmp_path: Path) -> None:
    _, caller_config = select_codex_textify_caller(repo_root() / "config.example.codex_cli.json")
    case = next(case for case in TEXTIFY_SMOKE_CASES if case.case_id == "R-ZIP-REPO-01")
    source = write_textify_smoke_fixture(case, tmp_path)
    request = build_textify_smoke_request(case, caller_config.name, source)
    assert source.sha256 is not None
    response = TextifyResponse(
        request_id=request.request_id,
        source=TextifiedSource(
            name=source.name,
            input_mime_type=source.mime_type,
            source_sha256=source.sha256,
            textification_required=True,
            status="unsupported_media",
            suggested_files=[],
            warnings=["unsupported media type for textify v1"],
        ),
        llm=None,
        warnings=[],
    )

    record = write_textify_smoke_artifacts(
        run_root=tmp_path,
        case=case,
        caller_config=caller_config,
        source=source,
        request=request,
        response=response,
        pricing=make_pricing(),
    )

    run_dir = tmp_path / "runs" / "R-ZIP-REPO-01" / "textifier_codex_gpt_54_mini"
    assert record["usage"] is None
    assert record["participates_in_model_ranking"] is False
    assert record["expected_status"] == "unsupported_media"
    assert not (run_dir / "usage.json").exists()
    assert (run_dir / "textified.md").read_text(encoding="utf-8") == ""
