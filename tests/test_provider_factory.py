from collections.abc import Mapping

import pytest

from curio.config import CurioConfig, ProviderConfig
from curio.llm_caller import (
    CodexCliAuthConfig,
    CodexCliClient,
    CodexCliCommand,
    CodexCliExecConfig,
    CodexCliRunResult,
    InMemorySecretStore,
    LlmConfigurationError,
    OpenAiApiAuthConfig,
    OpenAiApiCallResult,
    OpenAiApiClient,
    ProviderCallTiming,
    ProviderClientFactory,
    ProviderName,
    SecretRef,
    build_provider_client,
)


def make_timing() -> ProviderCallTiming:
    return ProviderCallTiming(
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:01Z",
        wall_seconds=1,
    )


class FakeCodexRunner:
    def run(self, command: CodexCliCommand, timeout_seconds: int) -> CodexCliRunResult:
        del command, timeout_seconds
        return CodexCliRunResult(stdout="", stderr="", return_code=0, timing=make_timing())


class FakeOpenAiTransport:
    def create_response(
        self,
        request_payload: Mapping[str, object],
        *,
        api_key: str,
        auth_config: OpenAiApiAuthConfig,
        timeout_seconds: int,
    ) -> OpenAiApiCallResult:
        del request_payload, api_key, auth_config, timeout_seconds
        return OpenAiApiCallResult(payload={}, timing=make_timing())


def make_secret_store() -> InMemorySecretStore:
    store = InMemorySecretStore()
    store.set_secret(SecretRef(service="curio/openai-api", account="default-api-key"), "sk-test")
    return store


def make_config() -> CurioConfig:
    return CurioConfig(
        providers={
            ProviderName.CODEX_CLI: ProviderConfig(
                auth_config=CodexCliAuthConfig(require_keyring_credentials_store=False),
                codex_exec_config=CodexCliExecConfig(executable="codex-test", sandbox="workspace-write"),
            ),
            ProviderName.OPENAI_API: ProviderConfig(
                auth_config=OpenAiApiAuthConfig(
                    api_key_ref=SecretRef(service="curio/openai-api", account="default-api-key"),
                    organization="org-test",
                    project="proj-test",
                )
            ),
        }
    )


def test_provider_client_factory_builds_codex_client_with_injected_config(tmp_path) -> None:
    runner = FakeCodexRunner()
    transport = FakeOpenAiTransport()
    secret_store = make_secret_store()
    factory = ProviderClientFactory(
        config=make_config(),
        secret_store=secret_store,
        codex_runner=runner,
        openai_transport=transport,
        codex_working_directory=tmp_path,
        codex_output_schema_dir=tmp_path,
    )

    client = factory.create(ProviderName.CODEX_CLI)

    assert isinstance(client, CodexCliClient)
    assert client.runner is runner
    assert client.exec_config.executable == "codex-test"
    assert client.auth_config.require_keyring_credentials_store is False
    assert client.working_directory == tmp_path
    assert client.output_schema_dir == tmp_path


def test_provider_client_factory_builds_openai_client_with_injected_config(tmp_path) -> None:
    transport = FakeOpenAiTransport()
    secret_store = make_secret_store()
    factory = ProviderClientFactory(
        config=make_config(),
        secret_store=secret_store,
        codex_runner=FakeCodexRunner(),
        openai_transport=transport,
        codex_working_directory=tmp_path,
    )

    client = factory.create("openai_api")

    assert isinstance(client, OpenAiApiClient)
    assert client.auth_config.organization == "org-test"
    assert client.auth_config.project == "proj-test"
    assert client.transport is transport
    assert client.secret_store is secret_store


def test_build_provider_client_requires_explicit_config_and_dependencies(tmp_path) -> None:
    runner = FakeCodexRunner()
    transport = FakeOpenAiTransport()
    secret_store = make_secret_store()

    client = build_provider_client(
        "codex_cli",
        make_config(),
        secret_store=secret_store,
        codex_runner=runner,
        openai_transport=transport,
        codex_working_directory=tmp_path,
    )

    assert isinstance(client, CodexCliClient)
    assert client.runner is runner
    assert client.working_directory == tmp_path


def test_provider_client_factory_rejects_missing_or_mismatched_provider_config(tmp_path) -> None:
    empty_config = CurioConfig(providers={})
    factory = ProviderClientFactory(
        config=empty_config,
        secret_store=make_secret_store(),
        codex_runner=FakeCodexRunner(),
        openai_transport=FakeOpenAiTransport(),
        codex_working_directory=tmp_path,
    )
    with pytest.raises(RuntimeError, match="providers.codex_cli"):
        factory.create("codex_cli")

    mismatched_codex = CurioConfig(
        providers={
            ProviderName.CODEX_CLI: ProviderConfig(
                auth_config=OpenAiApiAuthConfig(),
                codex_exec_config=CodexCliExecConfig(),
            )
        }
    )
    with pytest.raises(LlmConfigurationError, match="codex_cli auth config is invalid"):
        ProviderClientFactory(
            config=mismatched_codex,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("codex_cli")

    missing_codex_exec = CurioConfig(
        providers={ProviderName.CODEX_CLI: ProviderConfig(auth_config=CodexCliAuthConfig())}
    )
    with pytest.raises(LlmConfigurationError, match="codex_cli exec config is required"):
        ProviderClientFactory(
            config=missing_codex_exec,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("codex_cli")

    mismatched_openai = CurioConfig(
        providers={ProviderName.OPENAI_API: ProviderConfig(auth_config=CodexCliAuthConfig())}
    )
    with pytest.raises(LlmConfigurationError, match="openai_api auth config is invalid"):
        ProviderClientFactory(
            config=mismatched_openai,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("openai_api")
