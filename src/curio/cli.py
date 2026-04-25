import typer

app = typer.Typer(
    help="Semantic labeling of iMsgX artifacts in preparation for a knowledgebase.",
    invoke_without_command=True,
)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Curio CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _reserved(command: str) -> None:
    typer.echo(f"{command} is reserved but not implemented yet.", err=True)
    raise typer.Exit(1)


@app.command("translate")
def translate() -> None:
    """Translate text into English."""
    _reserved("translate")


@app.command("curate")
def curate() -> None:
    """Run the main Curio curation workflow."""
    _reserved("curate")


@app.command("bootstrap")
def bootstrap() -> None:
    """Bootstrap the label registry."""
    _reserved("bootstrap")


@app.command("schema")
def schema() -> None:
    """Validate or inspect Curio schemas."""
    _reserved("schema")


@app.command("doctor")
def doctor() -> None:
    """Diagnose local Curio configuration and provider prerequisites."""
    _reserved("doctor")
