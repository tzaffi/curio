import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from curio.cli import app
from curio.llm_caller import (
    KeyringSecretStore,
    LlmCallerError,
    ProviderName,
    SdkOpenAiApiTransport,
    SubprocessCodexCliRunner,
    build_llm_caller_client,
)
from curio.textify import TextifyError
from textify_smoke_helpers import (
    DEFAULT_TEXTIFY_SMOKE_ROOT,
    REPO_ROOT,
    TEXTIFY_SMOKE_CALLERS,
    TEXTIFY_SMOKE_CASES,
    build_smoke_textify_service,
    build_textify_smoke_request,
    redacted_caller_summary,
    select_codex_textify_caller,
    write_textify_smoke_artifacts,
    write_textify_smoke_fixture,
)

CONFIG_PATH = REPO_ROOT / "config.example.codex_cli.json"
LIVE_OPERATOR_GUIDANCE = (
    "Live Codex CLI textify smoke test failed. Confirm CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS=1, "
    "`codex` is installed, Codex CLI is logged in with ChatGPT auth, network access is available, "
    "fixtures are under the repository working directory, and config.example.codex_cli.json contains the selected "
    "llm_callers.NAME."
)


@pytest.fixture(scope="session")
def textify_smoke_run_root() -> Path:
    run_id = os.environ.get("CURIO_TEXTIFY_SMOKE_RUN_ID")
    if run_id is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"{timestamp}-{_short_git_sha()}"
    run_root = DEFAULT_TEXTIFY_SMOKE_ROOT / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "schemas").mkdir(parents=True, exist_ok=True)
    _write_manifest(run_root)
    return run_root


@pytest.mark.live_codex_cli_textify
@pytest.mark.parametrize("case", TEXTIFY_SMOKE_CASES, ids=lambda case: case.case_id)
@pytest.mark.parametrize("caller", TEXTIFY_SMOKE_CALLERS)
def test_live_codex_cli_textify_case_matrix(textify_smoke_run_root: Path, case, caller: str) -> None:
    config, caller_config = select_codex_textify_caller(CONFIG_PATH, caller)
    assert caller_config.pricing_config is not None
    source = write_textify_smoke_fixture(case, textify_smoke_run_root)
    request = build_textify_smoke_request(case, caller, source)
    service = build_smoke_textify_service(
        build_llm_caller_client(
            caller,
            config,
            secret_store=KeyringSecretStore(),
            codex_runner=SubprocessCodexCliRunner(),
            openai_transport=SdkOpenAiApiTransport(),
            codex_working_directory=REPO_ROOT,
            codex_output_schema_dir=textify_smoke_run_root / "schemas",
        ),
        caller_config,
    )

    try:
        response = service.textify(request)
    except (LlmCallerError, TextifyError) as exc:
        pytest.fail(f"{LIVE_OPERATOR_GUIDANCE}\nOriginal error: {exc}")

    write_textify_smoke_artifacts(
        run_root=textify_smoke_run_root,
        case=case,
        caller_config=caller_config,
        source=source,
        request=request,
        response=response,
        pricing=caller_config.pricing_config,
    )
    assert response.request_id == request.request_id
    assert response.llm is not None
    assert response.llm.provider == ProviderName.CODEX_CLI
    assert response.llm.model == caller_config.model
    if case.expected_suggested_paths:
        suggested_paths = [suggested_file.suggested_path for suggested_file in response.source.suggested_files]
        assert suggested_paths


@pytest.mark.live_codex_cli_textify
def test_live_codex_cli_textify_cli_default_and_explicit_caller(textify_smoke_run_root: Path) -> None:
    runner = CliRunner()
    case = TEXTIFY_SMOKE_CASES[0]
    source = write_textify_smoke_fixture(case, textify_smoke_run_root)
    source_path = source.path
    default_result = runner.invoke(
        app,
        [
            "textify",
            "--config",
            str(CONFIG_PATH),
            "--json",
            "--preferred-output-format",
            case.preferred_output_format,
            source_path,
        ],
    )
    explicit_result = runner.invoke(
        app,
        [
            "textify",
            "--config",
            str(CONFIG_PATH),
            "--json",
            "--preferred-output-format",
            case.preferred_output_format,
            "--llm-caller",
            "textifier_codex_gpt_54_mini",
            "--input-file",
            source_path,
        ],
    )

    _write_cli_result(textify_smoke_run_root, "default-caller", default_result.output)
    _write_cli_result(textify_smoke_run_root, "explicit-caller", explicit_result.output)
    _assert_cli_success(default_result.exit_code, default_result.output, "configured textify.llm_caller")
    _assert_cli_success(explicit_result.exit_code, explicit_result.output, "explicit --llm-caller")
    default_payload = json.loads(default_result.output)
    explicit_payload = json.loads(explicit_result.output)
    assert default_payload["llm"]["provider"] == ProviderName.CODEX_CLI
    assert explicit_payload["llm"]["provider"] == ProviderName.CODEX_CLI
    assert default_payload["llm"]["model"] == "gpt-5.4-mini"
    assert explicit_payload["llm"]["model"] == "gpt-5.4-mini"
    assert default_payload["source"]["suggested_files"]
    assert explicit_payload["source"]["suggested_files"]


def _write_manifest(run_root: Path) -> None:
    _, caller_config = select_codex_textify_caller(CONFIG_PATH)
    caller_summaries: list[dict[str, Any]] = []
    for caller in TEXTIFY_SMOKE_CALLERS:
        _, current_caller_config = select_codex_textify_caller(CONFIG_PATH, caller)
        caller_summaries.append(redacted_caller_summary(current_caller_config))
    manifest = {
        "run_root": str(run_root),
        "git_commit": _git_commit(),
        "config_path": str(CONFIG_PATH.relative_to(REPO_ROOT)),
        "environment_opt_ins": {
            "CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS": os.environ.get("CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS")
        },
        "selected_cases": [case.case_id for case in TEXTIFY_SMOKE_CASES],
        "selected_callers": list(TEXTIFY_SMOKE_CALLERS),
        "default_caller": caller_config.name,
        "redacted_callers": caller_summaries,
    }
    (run_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_cli_result(run_root: Path, name: str, output: str) -> None:
    cli_dir = run_root / "cli"
    cli_dir.mkdir(parents=True, exist_ok=True)
    (cli_dir / f"{name}.stdout").write_text(output, encoding="utf-8")


def _assert_cli_success(exit_code: int, output: str, label: str) -> None:
    if exit_code != 0:
        pytest.fail(f"{LIVE_OPERATOR_GUIDANCE}\nCLI path: {label}\nExit code: {exit_code}\nOutput:\n{output}")


def _short_git_sha() -> str:
    commit = _git_commit()
    return "nogit" if commit is None else commit[:12]


def _git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    commit = completed.stdout.strip()
    return commit or None
