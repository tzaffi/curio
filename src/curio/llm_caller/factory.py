from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from curio.llm_caller.auth import (
    CodexCliAuthConfig,
    GoogleDocumentAiAuthConfig,
    OpenAiApiAuthConfig,
    ProviderAuthConfig,
    SecretStore,
)
from curio.llm_caller.codex_cli import (
    CodexCliClient,
    CodexCliExecConfig,
    CodexCliRunner,
)
from curio.llm_caller.google_document_ai import (
    GoogleDocumentAiClient,
    GoogleDocumentAiTransport,
    SdkGoogleDocumentAiTransport,
)
from curio.llm_caller.models import LlmClient, LlmConfigurationError, ProviderName
from curio.llm_caller.openai_api import (
    OpenAiApiClient,
    OpenAiApiTransport,
    OpenAiResponsesConfig,
)


class LlmCallerConfigRecord(Protocol):
    name: str
    provider: ProviderName | str
    model: str
    auth_config: ProviderAuthConfig
    timeout_seconds: int
    codex_exec_config: CodexCliExecConfig | None
    openai_responses_config: OpenAiResponsesConfig | None


class LlmCallerConfigResolver(Protocol):
    def llm_caller_config(self, name: str) -> LlmCallerConfigRecord: ...


@dataclass(frozen=True, slots=True)
class LlmCallerFactory:
    config: LlmCallerConfigResolver
    secret_store: SecretStore
    codex_runner: CodexCliRunner
    openai_transport: OpenAiApiTransport
    codex_working_directory: Path
    google_document_ai_transport: GoogleDocumentAiTransport = field(default_factory=SdkGoogleDocumentAiTransport)
    codex_output_schema_dir: Path | None = None

    def create(self, name: str) -> LlmClient:
        caller_config = self.config.llm_caller_config(name)
        provider_name = ProviderName(caller_config.provider)
        if provider_name == ProviderName.CODEX_CLI:
            if caller_config.codex_exec_config is None:
                raise LlmConfigurationError("codex_cli exec config is required")
            if not isinstance(caller_config.auth_config, CodexCliAuthConfig):
                raise LlmConfigurationError("codex_cli auth config is invalid")
            return CodexCliClient(
                runner=self.codex_runner,
                exec_config=caller_config.codex_exec_config,
                auth_config=caller_config.auth_config,
                working_directory=self.codex_working_directory,
                model=caller_config.model,
                timeout_seconds=caller_config.timeout_seconds,
                output_schema_dir=self.codex_output_schema_dir,
            )
        if provider_name == ProviderName.GOOGLE_DOCUMENT_AI:
            if not isinstance(caller_config.auth_config, GoogleDocumentAiAuthConfig):
                raise LlmConfigurationError("google_document_ai auth config is invalid")
            return GoogleDocumentAiClient(
                transport=self.google_document_ai_transport,
                auth_config=caller_config.auth_config,
                model=caller_config.model,
                timeout_seconds=caller_config.timeout_seconds,
            )
        if not isinstance(caller_config.auth_config, OpenAiApiAuthConfig):
            raise LlmConfigurationError("openai_api auth config is invalid")
        return OpenAiApiClient(
            transport=self.openai_transport,
            auth_config=caller_config.auth_config,
            secret_store=self.secret_store,
            model=caller_config.model,
            timeout_seconds=caller_config.timeout_seconds,
            responses_config=caller_config.openai_responses_config,
        )


def build_llm_caller_client(
    name: str,
    config: LlmCallerConfigResolver,
    *,
    secret_store: SecretStore,
    codex_runner: CodexCliRunner,
    openai_transport: OpenAiApiTransport,
    codex_working_directory: Path,
    google_document_ai_transport: GoogleDocumentAiTransport | None = None,
    codex_output_schema_dir: Path | None = None,
) -> LlmClient:
    return LlmCallerFactory(
        config=config,
        secret_store=secret_store,
        codex_runner=codex_runner,
        openai_transport=openai_transport,
        google_document_ai_transport=(
            SdkGoogleDocumentAiTransport() if google_document_ai_transport is None else google_document_ai_transport
        ),
        codex_working_directory=codex_working_directory,
        codex_output_schema_dir=codex_output_schema_dir,
    ).create(name)
