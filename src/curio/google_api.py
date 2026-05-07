import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Protocol, cast

import keyring
from google.auth.external_account_authorized_user import (
    Credentials as ExternalAccountAuthorizedUserCredentials,
)
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials as AuthorizedUserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow, WSGITimeoutError
from keyring import errors as keyring_errors
from oauthlib.oauth2.rfc6749.errors import AccessDeniedError

from curio.config import GoogleConfig

GOOGLE_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
GOOGLE_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive"
GOOGLE_PIPELINE_SCOPES = (GOOGLE_SHEETS_SCOPE, GOOGLE_DRIVE_SCOPE)
GOOGLE_OAUTH_LOCAL_SERVER_TIMEOUT_SECONDS = 120

StoredGoogleCredentials = AuthorizedUserCredentials | ExternalAccountAuthorizedUserCredentials


class GoogleResponse(Protocol):
    status_code: int
    reason: str
    text: str

    def json(self) -> object: ...


class GoogleSession(Protocol):
    def get(self, url: str, *, params: Mapping[str, str]) -> GoogleResponse: ...

    def post(
        self,
        url: str,
        *,
        params: Mapping[str, str],
        json: Mapping[str, object] | None = None,
        data: bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> GoogleResponse: ...

    def put(
        self,
        url: str,
        *,
        params: Mapping[str, str],
        json: Mapping[str, object],
    ) -> GoogleResponse: ...

    def delete(self, url: str, *, params: Mapping[str, str]) -> GoogleResponse: ...


class GoogleApiError(RuntimeError):
    pass


def build_authorized_session(config: GoogleConfig, *, scopes: Sequence[str]) -> AuthorizedSession:
    credentials = load_credentials(config, scopes=scopes)
    return AuthorizedSession(credentials)


def load_credentials(config: GoogleConfig, *, scopes: Sequence[str]) -> StoredGoogleCredentials:
    if not config.oauth_client_credentials_path.exists():
        raise GoogleApiError(
            f"Missing Google OAuth client credential file at {config.oauth_client_credentials_path}"
        )

    normalized_scopes = normalize_scopes(scopes)
    credentials_json = read_authorized_user_credentials_json(config)
    existing_scopes = stored_scopes(credentials_json) if credentials_json is not None else ()
    credentials = (
        credentials_from_json(credentials_json, scopes=existing_scopes)
        if credentials_json is not None and set(normalized_scopes).issubset(existing_scopes)
        else None
    )

    if credentials is not None and credentials.valid:
        return credentials

    if credentials is not None and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        store_credentials(config, credentials)
        return credentials

    flow = InstalledAppFlow.from_client_secrets_file(
        str(config.oauth_client_credentials_path),
        scopes=list(merge_scopes(normalized_scopes, existing_scopes)),
    )
    try:
        credentials = flow.run_local_server(
            port=0,
            timeout_seconds=GOOGLE_OAUTH_LOCAL_SERVER_TIMEOUT_SECONDS,
        )
    except AccessDeniedError as exc:
        raise GoogleApiError(google_oauth_access_denied_message(normalized_scopes)) from exc
    except WSGITimeoutError as exc:
        raise GoogleApiError(google_oauth_timeout_message(normalized_scopes)) from exc
    store_credentials(config, credentials)
    return cast(StoredGoogleCredentials, credentials)


def credentials_from_json(payload: str, *, scopes: Sequence[str]) -> AuthorizedUserCredentials:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise GoogleApiError("Stored Google authorization state is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise GoogleApiError("Stored Google authorization state must be a JSON object.")
    return AuthorizedUserCredentials.from_authorized_user_info(data, scopes=list(scopes))


def store_credentials(config: GoogleConfig, credentials: StoredGoogleCredentials) -> None:
    try:
        keyring.set_password(
            config.authorized_user_keychain.service,
            config.authorized_user_keychain.account,
            credentials.to_json(),
        )
    except keyring_errors.KeyringError as exc:
        raise GoogleApiError(
            "Unable to write Google authorized-user credentials to macOS Keychain."
        ) from exc


def read_authorized_user_credentials_json(config: GoogleConfig) -> str | None:
    try:
        return keyring.get_password(
            config.authorized_user_keychain.service,
            config.authorized_user_keychain.account,
        )
    except keyring_errors.KeyringError as exc:
        raise GoogleApiError(
            "Unable to read Google authorized-user credentials from macOS Keychain."
        ) from exc


def stored_scopes_cover(payload: str, scopes: Sequence[str]) -> bool:
    stored_scope_values = stored_scopes(payload)
    if not stored_scope_values:
        return False
    return set(scopes).issubset(stored_scope_values)


def stored_scopes(payload: str) -> tuple[str, ...]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return ()
    if not isinstance(data, dict):
        return ()

    stored = data.get("scopes")
    if isinstance(stored, list):
        return normalize_scopes(value for value in stored if isinstance(value, str))
    elif isinstance(data.get("scope"), str):
        return normalize_scopes(str(data["scope"]).split())
    return ()


def normalize_scopes(scopes: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(scopes))


def merge_scopes(*scope_groups: Sequence[str]) -> tuple[str, ...]:
    merged: list[str] = []
    for scope_group in scope_groups:
        merged.extend(scope_group)
    return normalize_scopes(merged)


def google_oauth_access_denied_message(scopes: Sequence[str]) -> str:
    formatted_scopes = ", ".join(scopes)
    return (
        "Google blocked the OAuth authorization request (access_denied). "
        "If the app is still in Testing, add your Google account as a test user in the "
        "Google Cloud project's OAuth consent screen. Also confirm that the required APIs "
        "are enabled and that the consent screen is configured for these scopes: "
        f"{formatted_scopes}"
    )


def google_oauth_timeout_message(scopes: Sequence[str]) -> str:
    formatted_scopes = ", ".join(scopes)
    return (
        "Google OAuth authorization did not complete before the local callback timed out. "
        "If the browser showed 'Access blocked' or 'access_denied', add your Google account "
        "as a test user while the app is in Testing and confirm that the required APIs are "
        "enabled for these scopes: "
        f"{formatted_scopes}"
    )


def raise_for_status(action: str, response: GoogleResponse) -> None:
    if response.status_code < 400:
        return

    detail = response.text.strip()
    if detail:
        raise GoogleApiError(f"Unable to {action}: HTTP {response.status_code} {response.reason}: {detail}")
    raise GoogleApiError(f"Unable to {action}: HTTP {response.status_code} {response.reason}")
