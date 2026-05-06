import json
from pathlib import Path

import pytest
from google_auth_oauthlib.flow import WSGITimeoutError
from keyring import errors as keyring_errors
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

from curio.config import GoogleConfig, KeychainLocator
from curio.google_api import (
    GOOGLE_SHEETS_SCOPE,
    GoogleApiError,
    build_authorized_session,
    credentials_from_json,
    google_oauth_access_denied_message,
    google_oauth_timeout_message,
    load_credentials,
    read_authorized_user_credentials_json,
    store_credentials,
    stored_scopes_cover,
)


class FakeCredentials:
    def __init__(self, *, valid: bool, expired: bool = False, refresh_token: str | None = None) -> None:
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refreshed = False

    def refresh(self, request) -> None:
        del request
        self.refreshed = True
        self.valid = True
        self.expired = False

    def to_json(self) -> str:
        return json.dumps({"token": "stored", "scopes": [GOOGLE_SHEETS_SCOPE]})


class FakeFlow:
    def __init__(self, credentials: FakeCredentials | None = None, exc: Exception | None = None) -> None:
        self.credentials = credentials or FakeCredentials(valid=True)
        self.exc = exc

    def run_local_server(self, *, port: int, timeout_seconds: int) -> FakeCredentials:
        assert port == 0
        assert timeout_seconds == 120
        if self.exc is not None:
            raise self.exc
        return self.credentials


def google_config(tmp_path: Path) -> GoogleConfig:
    credentials_path = tmp_path / "client.json"
    credentials_path.write_text("{}", encoding="utf-8")
    return GoogleConfig(
        oauth_client_credentials_path=credentials_path,
        authorized_user_keychain=KeychainLocator(service="svc", account="acct"),
    )


def test_build_authorized_session_uses_loaded_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    loaded = FakeCredentials(valid=True)
    seen: list[object] = []
    monkeypatch.setattr("curio.google_api.load_credentials", lambda config, scopes: loaded)
    monkeypatch.setattr("curio.google_api.AuthorizedSession", lambda credentials: seen.append(credentials) or "session")

    assert build_authorized_session(google_config(tmp_path), scopes=[GOOGLE_SHEETS_SCOPE]) == "session"
    assert seen == [loaded]


def test_credentials_from_json_and_scope_validation() -> None:
    payload = json.dumps(
        {
            "token": "token",
            "refresh_token": "refresh",
            "client_id": "client",
            "client_secret": "secret",
            "scopes": [GOOGLE_SHEETS_SCOPE, "extra"],
        }
    )

    credentials = credentials_from_json(payload, scopes=[GOOGLE_SHEETS_SCOPE])

    assert credentials.refresh_token == "refresh"
    assert stored_scopes_cover(payload, [GOOGLE_SHEETS_SCOPE]) is True
    assert stored_scopes_cover(json.dumps({"scope": f"{GOOGLE_SHEETS_SCOPE} extra"}), [GOOGLE_SHEETS_SCOPE]) is True
    assert stored_scopes_cover(json.dumps({"scopes": ["other"]}), [GOOGLE_SHEETS_SCOPE]) is False
    assert stored_scopes_cover(json.dumps({"token": "token"}), [GOOGLE_SHEETS_SCOPE]) is False
    assert stored_scopes_cover("not-json", [GOOGLE_SHEETS_SCOPE]) is False
    assert stored_scopes_cover("[]", [GOOGLE_SHEETS_SCOPE]) is False

    with pytest.raises(GoogleApiError, match="not valid JSON"):
        credentials_from_json("not-json", scopes=[GOOGLE_SHEETS_SCOPE])
    with pytest.raises(GoogleApiError, match="JSON object"):
        credentials_from_json("[]", scopes=[GOOGLE_SHEETS_SCOPE])


def test_load_credentials_requires_client_secret_file(tmp_path: Path) -> None:
    config = GoogleConfig(
        oauth_client_credentials_path=tmp_path / "missing.json",
        authorized_user_keychain=KeychainLocator(service="svc", account="acct"),
    )

    with pytest.raises(GoogleApiError, match="Missing Google OAuth client credential file"):
        load_credentials(config, scopes=[GOOGLE_SHEETS_SCOPE])


def test_load_credentials_reuses_valid_keychain_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    credentials = FakeCredentials(valid=True)
    monkeypatch.setattr("curio.google_api.read_authorized_user_credentials_json", lambda config: "stored")
    monkeypatch.setattr("curio.google_api.stored_scopes_cover", lambda payload, scopes: True)
    monkeypatch.setattr("curio.google_api.credentials_from_json", lambda payload, scopes: credentials)

    assert load_credentials(google_config(tmp_path), scopes=[GOOGLE_SHEETS_SCOPE]) is credentials


def test_load_credentials_refreshes_expired_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    credentials = FakeCredentials(valid=False, expired=True, refresh_token="refresh")
    stored: list[FakeCredentials] = []
    monkeypatch.setattr("curio.google_api.read_authorized_user_credentials_json", lambda config: "stored")
    monkeypatch.setattr("curio.google_api.stored_scopes_cover", lambda payload, scopes: True)
    monkeypatch.setattr("curio.google_api.credentials_from_json", lambda payload, scopes: credentials)
    monkeypatch.setattr("curio.google_api.store_credentials", lambda config, refreshed: stored.append(refreshed))

    loaded = load_credentials(google_config(tmp_path), scopes=[GOOGLE_SHEETS_SCOPE])

    assert loaded is credentials
    assert credentials.refreshed is True
    assert stored == [credentials]


def test_load_credentials_runs_oauth_when_missing_or_scope_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    oauth_credentials = FakeCredentials(valid=True)
    stored: list[FakeCredentials] = []
    seen_scopes: list[list[str]] = []

    class FakeInstalledAppFlow:
        @staticmethod
        def from_client_secrets_file(path: str, scopes: list[str]) -> FakeFlow:
            assert path == str(google_config(tmp_path).oauth_client_credentials_path)
            seen_scopes.append(scopes)
            return FakeFlow(oauth_credentials)

    monkeypatch.setattr("curio.google_api.read_authorized_user_credentials_json", lambda config: "stored")
    monkeypatch.setattr("curio.google_api.stored_scopes_cover", lambda payload, scopes: False)
    monkeypatch.setattr("curio.google_api.InstalledAppFlow", FakeInstalledAppFlow)
    monkeypatch.setattr("curio.google_api.store_credentials", lambda config, credentials: stored.append(credentials))

    loaded = load_credentials(google_config(tmp_path), scopes=[GOOGLE_SHEETS_SCOPE, GOOGLE_SHEETS_SCOPE])

    assert loaded is oauth_credentials
    assert stored == [oauth_credentials]
    assert seen_scopes == [[GOOGLE_SHEETS_SCOPE]]


@pytest.mark.parametrize(
    ("exc", "message"),
    [
        (AccessDeniedError(), "access_denied"),
        (WSGITimeoutError(), "did not complete"),
    ],
)
def test_load_credentials_reports_oauth_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    exc: Exception,
    message: str,
) -> None:
    class FakeInstalledAppFlow:
        @staticmethod
        def from_client_secrets_file(path: str, scopes: list[str]) -> FakeFlow:
            del path, scopes
            return FakeFlow(exc=exc)

    monkeypatch.setattr("curio.google_api.read_authorized_user_credentials_json", lambda config: None)
    monkeypatch.setattr("curio.google_api.InstalledAppFlow", FakeInstalledAppFlow)

    with pytest.raises(GoogleApiError, match=message):
        load_credentials(google_config(tmp_path), scopes=[GOOGLE_SHEETS_SCOPE])


def test_keychain_read_write_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    writes: list[tuple[str, str, str]] = []
    monkeypatch.setattr("curio.google_api.keyring.get_password", lambda service, account: "stored-json")
    monkeypatch.setattr(
        "curio.google_api.keyring.set_password",
        lambda service, account, password: writes.append((service, account, password)),
    )
    config = google_config(tmp_path)
    credentials = FakeCredentials(valid=True)

    assert read_authorized_user_credentials_json(config) == "stored-json"
    store_credentials(config, credentials)
    assert writes == [("svc", "acct", credentials.to_json())]

    monkeypatch.setattr(
        "curio.google_api.keyring.get_password",
        lambda service, account: (_ for _ in ()).throw(keyring_errors.KeyringError("boom")),
    )
    with pytest.raises(GoogleApiError, match="Unable to read"):
        read_authorized_user_credentials_json(config)

    monkeypatch.setattr(
        "curio.google_api.keyring.set_password",
        lambda service, account, password: (_ for _ in ()).throw(keyring_errors.KeyringError("boom")),
    )
    with pytest.raises(GoogleApiError, match="Unable to write"):
        store_credentials(config, credentials)


def test_oauth_guidance_messages_include_scopes() -> None:
    assert GOOGLE_SHEETS_SCOPE in google_oauth_access_denied_message([GOOGLE_SHEETS_SCOPE])
    assert GOOGLE_SHEETS_SCOPE in google_oauth_timeout_message([GOOGLE_SHEETS_SCOPE])
