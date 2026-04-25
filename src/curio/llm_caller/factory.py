from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from curio.llm_caller.auth import (
    CodexCliAuthConfig,
    OpenAiApiAuthConfig,
    ProviderAuthConfig,
    SecretStore,
)
from curio.llm_caller.codex_cli import (
    CodexCliClient,
    CodexCliExecConfig,
    CodexCliRunner,
)
from curio.llm_caller.models import LlmClient, LlmConfigurationError, ProviderName
from curio.llm_caller.openai_api import OpenAiApiClient, OpenAiApiTransport


class ProviderConfigRecord(Protocol):
    auth_config: ProviderAuthConfig
    codex_exec_config: CodexCliExecConfig | None


class ProviderConfigResolver(Protocol):
    def provider_config(self, provider: ProviderName | str) -> ProviderConfigRecord: ...


@dataclass(frozen=True, slots=True)
class ProviderClientFactory:
    config: ProviderConfigResolver
    secret_store: SecretStore
    codex_runner: CodexCliRunner
    openai_transport: OpenAiApiTransport
    codex_working_directory: Path
    codex_output_schema_dir: Path | None = None

    def create(self, provider: ProviderName | str) -> LlmClient:
        provider_name = ProviderName(provider)
        provider_config = self.config.provider_config(provider_name)
        if provider_name == ProviderName.CODEX_CLI:
            if provider_config.codex_exec_config is None:
                raise LlmConfigurationError("codex_cli exec config is required")
            if not isinstance(provider_config.auth_config, CodexCliAuthConfig):
                raise LlmConfigurationError("codex_cli auth config is invalid")
            return CodexCliClient(
                runner=self.codex_runner,
                exec_config=provider_config.codex_exec_config,
                auth_config=provider_config.auth_config,
                working_directory=self.codex_working_directory,
                output_schema_dir=self.codex_output_schema_dir,
            )
        if not isinstance(provider_config.auth_config, OpenAiApiAuthConfig):
            raise LlmConfigurationError("openai_api auth config is invalid")
        return OpenAiApiClient(
            transport=self.openai_transport,
            auth_config=provider_config.auth_config,
            secret_store=self.secret_store,
        )


def build_provider_client(
    provider: ProviderName | str,
    config: ProviderConfigResolver,
    *,
    secret_store: SecretStore,
    codex_runner: CodexCliRunner,
    openai_transport: OpenAiApiTransport,
    codex_working_directory: Path,
    codex_output_schema_dir: Path | None = None,
) -> LlmClient:
    return ProviderClientFactory(
        config=config,
        secret_store=secret_store,
        codex_runner=codex_runner,
        openai_transport=openai_transport,
        codex_working_directory=codex_working_directory,
        codex_output_schema_dir=codex_output_schema_dir,
    ).create(provider)
