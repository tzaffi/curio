from typer.testing import CliRunner

from curio.cli import app

runner = CliRunner()


def test_root_without_subcommand_shows_help() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "Semantic labeling of iMsgX artifacts" in result.output
    assert "translate" in result.output
    assert "curate" in result.output
    assert "bootstrap" in result.output
    assert "schema" in result.output
    assert "doctor" in result.output


def test_root_help_shows_reserved_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "translate" in result.output
    assert "curate" in result.output
    assert "bootstrap" in result.output
    assert "schema" in result.output
    assert "doctor" in result.output


def test_reserved_commands_report_stub_status() -> None:
    for command in ("translate", "curate", "bootstrap", "schema", "doctor"):
        result = runner.invoke(app, [command])

        assert result.exit_code == 1
        assert f"{command} is reserved but not implemented yet." in result.output
