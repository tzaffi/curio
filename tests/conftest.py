import os
from collections.abc import Mapping

import pytest

LIVE_CODEX_CLI_ENV_VAR = "CURIO_LIVE_CODEX_CLI_TESTS"
LIVE_CODEX_CLI_MARKER = "live_codex_cli"
LIVE_CODEX_CLI_SKIP_REASON = "set CURIO_LIVE_CODEX_CLI_TESTS=1 to run Codex CLI live smoke tests"
LIVE_CODEX_CLI_TEXTIFY_ENV_VAR = "CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS"
LIVE_CODEX_CLI_TEXTIFY_MARKER = "live_codex_cli_textify"
LIVE_CODEX_CLI_TEXTIFY_SKIP_REASON = (
    "set CURIO_LIVE_CODEX_CLI_TEXTIFY_TESTS=1 to run Codex CLI textify live smoke tests"
)


def live_codex_cli_tests_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return env.get(LIVE_CODEX_CLI_ENV_VAR) == "1"


def live_codex_cli_textify_tests_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return env.get(LIVE_CODEX_CLI_TEXTIFY_ENV_VAR) == "1"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_live_codex_cli = pytest.mark.skip(reason=LIVE_CODEX_CLI_SKIP_REASON)
    skip_live_codex_cli_textify = pytest.mark.skip(reason=LIVE_CODEX_CLI_TEXTIFY_SKIP_REASON)
    for item in items:
        if not live_codex_cli_tests_enabled() and list(item.iter_markers(name=LIVE_CODEX_CLI_MARKER)):
            item.add_marker(skip_live_codex_cli)
        if not live_codex_cli_textify_tests_enabled() and list(
            item.iter_markers(name=LIVE_CODEX_CLI_TEXTIFY_MARKER)
        ):
            item.add_marker(skip_live_codex_cli_textify)
