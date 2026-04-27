import tomllib
from pathlib import Path

import pytest

import conftest


class FakeItem:
    def __init__(self, *, marked: bool = False, marker_name: str | None = None) -> None:
        self.marked = marked
        self.marker_name = marker_name or conftest.LIVE_CODEX_CLI_MARKER
        self.added_markers: list[pytest.MarkDecorator] = []

    def iter_markers(self, name: str | None = None) -> list[object]:
        if self.marked and name in (None, self.marker_name):
            return [object()]
        return []

    def add_marker(self, marker: pytest.MarkDecorator) -> None:
        self.added_markers.append(marker)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_pyproject_registers_live_codex_cli_marker() -> None:
    pyproject = tomllib.loads((repo_root() / "pyproject.toml").read_text(encoding="utf-8"))

    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]

    assert any(marker.startswith(f"{conftest.LIVE_CODEX_CLI_MARKER}:") for marker in markers)
    assert any(marker.startswith(f"{conftest.LIVE_CODEX_CLI_TEXTIFY_MARKER}:") for marker in markers)


@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        (None, False),
        ("", False),
        ("0", False),
        ("true", False),
        ("yes", False),
        ("1", True),
    ],
)
def test_live_codex_cli_opt_in_requires_exact_one(env_value: str | None, expected: bool) -> None:
    environ = {} if env_value is None else {conftest.LIVE_CODEX_CLI_ENV_VAR: env_value}

    assert conftest.live_codex_cli_tests_enabled(environ) is expected
    textify_environ = {} if env_value is None else {conftest.LIVE_CODEX_CLI_TEXTIFY_ENV_VAR: env_value}
    assert conftest.live_codex_cli_textify_tests_enabled(textify_environ) is expected


def test_collection_skips_marked_tests_when_live_codex_cli_is_not_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(conftest.LIVE_CODEX_CLI_ENV_VAR, raising=False)
    monkeypatch.delenv(conftest.LIVE_CODEX_CLI_TEXTIFY_ENV_VAR, raising=False)
    marked = FakeItem(marked=True)
    textify_marked = FakeItem(marked=True, marker_name=conftest.LIVE_CODEX_CLI_TEXTIFY_MARKER)
    unmarked = FakeItem(marked=False)

    conftest.pytest_collection_modifyitems(config=None, items=[marked, textify_marked, unmarked])  # type: ignore[arg-type]

    assert len(marked.added_markers) == 1
    assert marked.added_markers[0].mark.name == "skip"
    assert marked.added_markers[0].mark.kwargs == {"reason": conftest.LIVE_CODEX_CLI_SKIP_REASON}
    assert textify_marked.added_markers[0].mark.kwargs == {"reason": conftest.LIVE_CODEX_CLI_TEXTIFY_SKIP_REASON}
    assert unmarked.added_markers == []


def test_collection_allows_marked_tests_when_live_codex_cli_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(conftest.LIVE_CODEX_CLI_ENV_VAR, "1")
    monkeypatch.setenv(conftest.LIVE_CODEX_CLI_TEXTIFY_ENV_VAR, "1")
    marked = FakeItem(marked=True)
    textify_marked = FakeItem(marked=True, marker_name=conftest.LIVE_CODEX_CLI_TEXTIFY_MARKER)
    unmarked = FakeItem(marked=False)

    conftest.pytest_collection_modifyitems(config=None, items=[marked, textify_marked, unmarked])  # type: ignore[arg-type]

    assert marked.added_markers == []
    assert textify_marked.added_markers == []
    assert unmarked.added_markers == []


def test_collection_skips_marked_tests_for_non_one_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(conftest.LIVE_CODEX_CLI_ENV_VAR, "true")
    marked = FakeItem(marked=True)

    conftest.pytest_collection_modifyitems(config=None, items=[marked])  # type: ignore[arg-type]

    assert len(marked.added_markers) == 1
