from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, cast

import keyring
from keyring import errors as keyring_errors

from curio.llm_caller.models import LlmAuthError, LlmConfigurationError, ProviderName

JsonObject = dict[str, object]

DEFAULT_OPENAI_API_KEY_SERVICE = "curio/openai-api"
DEFAULT_OPENAI_API_KEY_ACCOUNT = "default-api-key"
DEFAULT_CODEX_API_KEY_SERVICE = "curio/codex-cli"
DEFAULT_CODEX_API_KEY_ACCOUNT = "default-api-key"
MISSING_CREDENTIAL_DETAIL = "credential not available"
SECURE_STORE_ACCESS_FAILED_DETAIL = "secure store access failed"


class SecretBackend(StrEnum):
    KEYRING = "keyring"


class CodexCliAuthMode(StrEnum):
    CHATGPT = "chatgpt"
    API_KEY = "api_key"


class GoogleDocumentAiProcessorKind(StrEnum):
    ENTERPRISE_DOCUMENT_OCR = "enterprise_document_ocr"
    LAYOUT_PARSER = "layout_parser"


class SecretLookupError(LlmAuthError):
    def __init__(self, detail: str, *, error_code: str) -> None:
        super().__init__(detail)
        self.detail = detail
        self.error_code = error_code


class ProviderAuthConfigError(LlmConfigurationError):
    pass


def _require_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


@dataclass(frozen=True, slots=True)
class SecretRef:
    service: str
    account: str
    label: str | None = None
    backend: SecretBackend | str = SecretBackend.KEYRING

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend", SecretBackend(self.backend))
        _require_string(self.service, "secret service")
        _require_string(self.account, "secret account")
        if self.label is not None:
            _require_string(self.label, "secret label")

    @classmethod
    def from_json(cls, value: object) -> "SecretRef":
        payload = _require_mapping(value, "secret ref")
        label = payload.get("label")
        return cls(
            backend=_require_string(_require_field(payload, "backend"), "secret backend"),
            service=_require_string(_require_field(payload, "service"), "secret service"),
            account=_require_string(_require_field(payload, "account"), "secret account"),
            label=None if label is None else _require_string(label, "secret label"),
        )

    def to_json(self) -> JsonObject:
        backend = cast(SecretBackend, self.backend)
        return {
            "backend": backend.value,
            "service": self.service,
            "account": self.account,
            "label": self.label,
        }


class SecretStore(Protocol):
    def get_secret(self, secret_ref: SecretRef) -> str: ...

    def invalidate(self, secret_ref: SecretRef | None = None) -> None: ...


def secret_ref_cache_key(secret_ref: SecretRef) -> tuple[str, str, str]:
    backend = cast(SecretBackend, secret_ref.backend)
    return (backend.value, secret_ref.service, secret_ref.account)


class InMemorySecretStore:
    def __init__(self, secrets: Mapping[tuple[str, str, str], str] | None = None) -> None:
        self._secrets = dict(secrets or {})

    def set_secret(self, secret_ref: SecretRef, value: str) -> None:
        _require_string(value, "secret")
        self._secrets[secret_ref_cache_key(secret_ref)] = value

    def get_secret(self, secret_ref: SecretRef) -> str:
        key = secret_ref_cache_key(secret_ref)
        if key not in self._secrets:
            raise SecretLookupError(
                MISSING_CREDENTIAL_DETAIL,
                error_code="credential_not_available",
            )
        return self._secrets[key]

    def invalidate(self, secret_ref: SecretRef | None = None) -> None:
        if secret_ref is None:
            self._secrets.clear()
            return
        self._secrets.pop(secret_ref_cache_key(secret_ref), None)


class KeyringSecretStore:
    def get_secret(self, secret_ref: SecretRef) -> str:
        try:
            secret = keyring.get_password(secret_ref.service, secret_ref.account)
        except keyring_errors.KeyringError as exc:
            raise SecretLookupError(
                SECURE_STORE_ACCESS_FAILED_DETAIL,
                error_code="secure_store_access_failed",
            ) from exc
        if not secret:
            raise SecretLookupError(
                MISSING_CREDENTIAL_DETAIL,
                error_code="credential_not_available",
            )
        return secret

    def invalidate(self, secret_ref: SecretRef | None = None) -> None:
        del secret_ref


def default_openai_api_key_ref() -> SecretRef:
    return SecretRef(
        service=DEFAULT_OPENAI_API_KEY_SERVICE,
        account=DEFAULT_OPENAI_API_KEY_ACCOUNT,
        label="OpenAI API key",
    )


def default_codex_api_key_ref() -> SecretRef:
    return SecretRef(
        service=DEFAULT_CODEX_API_KEY_SERVICE,
        account=DEFAULT_CODEX_API_KEY_ACCOUNT,
        label="Codex CLI API key",
    )


@dataclass(frozen=True, slots=True)
class OpenAiApiAuthConfig:
    api_key_ref: SecretRef = field(default_factory=default_openai_api_key_ref)
    organization: str | None = None
    project: str | None = None
    provider: ProviderName = field(default=ProviderName.OPENAI_API, init=False)

    def __post_init__(self) -> None:
        if self.organization is not None:
            _require_string(self.organization, "organization")
        if self.project is not None:
            _require_string(self.project, "project")

    @classmethod
    def from_json(cls, value: object) -> "OpenAiApiAuthConfig":
        payload = _require_mapping(value, "openai_api auth config")
        provider = ProviderName(_require_string(_require_field(payload, "provider"), "provider"))
        if provider != ProviderName.OPENAI_API:
            raise ProviderAuthConfigError("provider must be openai_api")
        organization = payload.get("organization")
        project = payload.get("project")
        return cls(
            api_key_ref=SecretRef.from_json(_require_field(payload, "api_key_ref")),
            organization=None if organization is None else _require_string(organization, "organization"),
            project=None if project is None else _require_string(project, "project"),
        )

    def to_json(self) -> JsonObject:
        return {
            "provider": self.provider.value,
            "api_key_ref": self.api_key_ref.to_json(),
            "organization": self.organization,
            "project": self.project,
        }


@dataclass(frozen=True, slots=True)
class CodexCliAuthConfig:
    mode: CodexCliAuthMode | str = CodexCliAuthMode.CHATGPT
    api_key_ref: SecretRef | None = None
    require_keyring_credentials_store: bool = True
    provider: ProviderName = field(default=ProviderName.CODEX_CLI, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", CodexCliAuthMode(self.mode))
        _require_bool(self.require_keyring_credentials_store, "require_keyring_credentials_store")
        mode = cast(CodexCliAuthMode, self.mode)
        if mode == CodexCliAuthMode.API_KEY and self.api_key_ref is None:
            object.__setattr__(self, "api_key_ref", default_codex_api_key_ref())
        if mode == CodexCliAuthMode.CHATGPT and self.api_key_ref is not None:
            raise ProviderAuthConfigError("codex_cli chatgpt auth must not include an api_key_ref")

    @classmethod
    def from_json(cls, value: object) -> "CodexCliAuthConfig":
        payload = _require_mapping(value, "codex_cli auth config")
        provider = ProviderName(_require_string(_require_field(payload, "provider"), "provider"))
        if provider != ProviderName.CODEX_CLI:
            raise ProviderAuthConfigError("provider must be codex_cli")
        api_key_ref = payload.get("api_key_ref")
        return cls(
            mode=_require_string(_require_field(payload, "mode"), "auth mode"),
            api_key_ref=None if api_key_ref is None else SecretRef.from_json(api_key_ref),
            require_keyring_credentials_store=_require_bool(
                _require_field(payload, "require_keyring_credentials_store"),
                "require_keyring_credentials_store",
            ),
        )

    def to_json(self) -> JsonObject:
        mode = cast(CodexCliAuthMode, self.mode)
        return {
            "provider": self.provider.value,
            "mode": mode.value,
            "api_key_ref": None if self.api_key_ref is None else self.api_key_ref.to_json(),
            "require_keyring_credentials_store": self.require_keyring_credentials_store,
        }


@dataclass(frozen=True, slots=True)
class GoogleDocumentAiAuthConfig:
    project_id: str
    location: str
    processor_id: str
    processor_version: str | None = None
    processor_kind: GoogleDocumentAiProcessorKind | str = GoogleDocumentAiProcessorKind.ENTERPRISE_DOCUMENT_OCR
    provider: ProviderName = field(default=ProviderName.GOOGLE_DOCUMENT_AI, init=False)

    def __post_init__(self) -> None:
        _require_string(self.project_id, "project_id")
        _require_string(self.location, "location")
        _require_string(self.processor_id, "processor_id")
        if self.processor_version is not None:
            _require_string(self.processor_version, "processor_version")
        object.__setattr__(
            self,
            "processor_kind",
            GoogleDocumentAiProcessorKind(self.processor_kind),
        )

    @classmethod
    def from_json(cls, value: object) -> "GoogleDocumentAiAuthConfig":
        payload = _require_mapping(value, "google_document_ai auth config")
        provider = ProviderName(_require_string(_require_field(payload, "provider"), "provider"))
        if provider != ProviderName.GOOGLE_DOCUMENT_AI:
            raise ProviderAuthConfigError("provider must be google_document_ai")
        processor_version = payload.get("processor_version")
        return cls(
            project_id=_require_string(_require_field(payload, "project_id"), "project_id"),
            location=_require_string(_require_field(payload, "location"), "location"),
            processor_id=_require_string(_require_field(payload, "processor_id"), "processor_id"),
            processor_version=None
            if processor_version is None
            else _require_string(processor_version, "processor_version"),
            processor_kind=_require_string(_require_field(payload, "processor_kind"), "processor_kind"),
        )

    def to_json(self) -> JsonObject:
        processor_kind = cast(GoogleDocumentAiProcessorKind, self.processor_kind)
        return {
            "provider": self.provider.value,
            "project_id": self.project_id,
            "location": self.location,
            "processor_id": self.processor_id,
            "processor_version": self.processor_version,
            "processor_kind": processor_kind.value,
        }


ProviderAuthConfig = OpenAiApiAuthConfig | CodexCliAuthConfig | GoogleDocumentAiAuthConfig


def resolve_openai_api_key(config: OpenAiApiAuthConfig, secret_store: SecretStore) -> str:
    return secret_store.get_secret(config.api_key_ref)


def resolve_codex_api_key(config: CodexCliAuthConfig, secret_store: SecretStore) -> str:
    mode = cast(CodexCliAuthMode, config.mode)
    if mode != CodexCliAuthMode.API_KEY:
        raise ProviderAuthConfigError("codex_cli auth mode does not use a Curio API key")
    return secret_store.get_secret(cast(SecretRef, config.api_key_ref))


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return cast(Mapping[str, object], value)


def _require_field(payload: Mapping[str, object], field_name: str) -> object:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    return payload[field_name]
