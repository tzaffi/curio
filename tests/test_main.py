from curio import __main__


def test_main_invokes_typer_app(monkeypatch) -> None:
    called = False

    def fake_app() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(__main__, "app", fake_app)

    __main__.main()

    assert called is True
