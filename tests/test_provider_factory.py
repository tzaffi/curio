from collections.abc import Mapping

import pytest

from curio.config import CurioConfig, LlmCallerConfig
from curio.llm_caller import (
    CodexCliAuthConfig,
    CodexCliClient,
    CodexCliCommand,
    CodexCliExecConfig,
    CodexCliReasoningEffort,
    CodexCliRunResult,
    GoogleDocumentAiAuthConfig,
    GoogleDocumentAiCallResult,
    GoogleDocumentAiClient,
    InMemorySecretStore,
    LlmCallerFactory,
    LlmConfigurationError,
    OpenAiApiAuthConfig,
    OpenAiApiCallResult,
    OpenAiApiClient,
    OpenAiResponsesConfig,
    ProviderCallTiming,
    ProviderName,
    SecretRef,
    UnsupportedCapabilityError,
    build_llm_caller_client,
)
from curio.translate import Block, TranslationRequest, TranslationService


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


class FakeGoogleDocumentAiTransport:
    def __init__(self) -> None:
        self.calls = 0

    def process_document(self, file_part, *, auth_config, timeout_seconds) -> GoogleDocumentAiCallResult:
        self.calls += 1
        del file_part, auth_config, timeout_seconds
        return GoogleDocumentAiCallResult(payload={"text": "hello"}, timing=make_timing())


def make_secret_store() -> InMemorySecretStore:
    store = InMemorySecretStore()
    store.set_secret(SecretRef(service="curio/openai-api", account="default-api-key"), "sk-test")
    return store


def make_config() -> CurioConfig:
    return CurioConfig(
        llm_callers={
            "translator_codex_gpt_55": LlmCallerConfig(
                name="translator_codex_gpt_55",
                provider=ProviderName.CODEX_CLI,
                model="gpt-5.5",
                auth_config=CodexCliAuthConfig(require_keyring_credentials_store=False),
                codex_exec_config=CodexCliExecConfig(executable="codex-test", sandbox="workspace-write"),
                timeout_seconds=111,
            ),
            "translator_codex_gpt_54_mini": LlmCallerConfig(
                name="translator_codex_gpt_54_mini",
                provider=ProviderName.CODEX_CLI,
                model="gpt-5.4-mini",
                auth_config=CodexCliAuthConfig(require_keyring_credentials_store=False),
                codex_exec_config=CodexCliExecConfig(
                    executable="codex-test",
                    sandbox="read-only",
                    model_reasoning_effort="minimal",
                ),
                timeout_seconds=222,
            ),
            "translator_openai_gpt_54_mini_cold": LlmCallerConfig(
                name="translator_openai_gpt_54_mini_cold",
                provider=ProviderName.OPENAI_API,
                model="gpt-5.4-mini",
                auth_config=OpenAiApiAuthConfig(
                    api_key_ref=SecretRef(service="curio/openai-api", account="default-api-key"),
                    organization="org-test",
                    project="proj-test",
                ),
                timeout_seconds=333,
                openai_responses_config=OpenAiResponsesConfig(temperature=0.2),
            ),
            "textifier_google_document_ai": LlmCallerConfig(
                name="textifier_google_document_ai",
                provider=ProviderName.GOOGLE_DOCUMENT_AI,
                model="document-ai-layout-parser",
                auth_config=GoogleDocumentAiAuthConfig("proj", "us", "processor"),
                timeout_seconds=444,
            ),
        }
    )


def test_llm_caller_factory_builds_codex_client_with_injected_config(tmp_path) -> None:
    runner = FakeCodexRunner()
    transport = FakeOpenAiTransport()
    secret_store = make_secret_store()
    factory = LlmCallerFactory(
        config=make_config(),
        secret_store=secret_store,
        codex_runner=runner,
        openai_transport=transport,
        codex_working_directory=tmp_path,
        codex_output_schema_dir=tmp_path,
    )

    client = factory.create("translator_codex_gpt_55")

    assert isinstance(client, CodexCliClient)
    assert client.runner is runner
    assert client.exec_config.executable == "codex-test"
    assert client.auth_config.require_keyring_credentials_store is False
    assert client.working_directory == tmp_path
    assert client.output_schema_dir == tmp_path
    assert client.model == "gpt-5.5"
    assert client.timeout_seconds == 111

    second_client = factory.create("translator_codex_gpt_54_mini")
    assert isinstance(second_client, CodexCliClient)
    assert second_client.model == "gpt-5.4-mini"
    assert second_client.timeout_seconds == 222
    assert second_client.exec_config.model_reasoning_effort == CodexCliReasoningEffort.MINIMAL


def test_llm_caller_factory_builds_openai_client_with_injected_config(tmp_path) -> None:
    transport = FakeOpenAiTransport()
    secret_store = make_secret_store()
    factory = LlmCallerFactory(
        config=make_config(),
        secret_store=secret_store,
        codex_runner=FakeCodexRunner(),
        openai_transport=transport,
        codex_working_directory=tmp_path,
    )

    client = factory.create("translator_openai_gpt_54_mini_cold")

    assert isinstance(client, OpenAiApiClient)
    assert client.auth_config.organization == "org-test"
    assert client.auth_config.project == "proj-test"
    assert client.transport is transport
    assert client.secret_store is secret_store
    assert client.model == "gpt-5.4-mini"
    assert client.timeout_seconds == 333
    assert client.responses_config.temperature == 0.2


def test_llm_caller_factory_builds_google_document_ai_client_with_injected_config(tmp_path) -> None:
    google_transport = FakeGoogleDocumentAiTransport()
    factory = LlmCallerFactory(
        config=make_config(),
        secret_store=make_secret_store(),
        codex_runner=FakeCodexRunner(),
        openai_transport=FakeOpenAiTransport(),
        google_document_ai_transport=google_transport,
        codex_working_directory=tmp_path,
    )

    client = factory.create("textifier_google_document_ai")

    assert isinstance(client, GoogleDocumentAiClient)
    assert client.transport is google_transport
    assert client.model == "document-ai-layout-parser"
    assert client.timeout_seconds == 444


def test_google_document_ai_caller_rejects_translation_before_transport(tmp_path) -> None:
    google_transport = FakeGoogleDocumentAiTransport()
    client = build_llm_caller_client(
        "textifier_google_document_ai",
        make_config(),
        secret_store=make_secret_store(),
        codex_runner=FakeCodexRunner(),
        openai_transport=FakeOpenAiTransport(),
        google_document_ai_transport=google_transport,
        codex_working_directory=tmp_path,
    )
    service = TranslationService(llm_client=client)
    request = TranslationRequest(
        request_id="translate-test",
        blocks=[Block(block_id=1, name="tweet_text", source_language_hint="ja", text="こんにちは")],
        llm_caller="textifier_google_document_ai",
    )

    with pytest.raises(UnsupportedCapabilityError, match="text_generation"):
        service.translate(request)
    assert google_transport.calls == 0


def test_build_llm_caller_client_requires_explicit_config_and_dependencies(tmp_path) -> None:
    runner = FakeCodexRunner()
    transport = FakeOpenAiTransport()
    secret_store = make_secret_store()

    client = build_llm_caller_client(
        "translator_codex_gpt_55",
        make_config(),
        secret_store=secret_store,
        codex_runner=runner,
        openai_transport=transport,
        codex_working_directory=tmp_path,
    )

    assert isinstance(client, CodexCliClient)
    assert client.runner is runner
    assert client.working_directory == tmp_path

    google_client = build_llm_caller_client(
        "textifier_google_document_ai",
        make_config(),
        secret_store=secret_store,
        codex_runner=runner,
        openai_transport=transport,
        google_document_ai_transport=FakeGoogleDocumentAiTransport(),
        codex_working_directory=tmp_path,
    )
    assert isinstance(google_client, GoogleDocumentAiClient)


def test_llm_caller_factory_rejects_missing_or_mismatched_caller_config(tmp_path) -> None:
    empty_config = CurioConfig(llm_callers={})
    factory = LlmCallerFactory(
        config=empty_config,
        secret_store=make_secret_store(),
        codex_runner=FakeCodexRunner(),
        openai_transport=FakeOpenAiTransport(),
        codex_working_directory=tmp_path,
    )
    with pytest.raises(RuntimeError, match="llm_callers.translator_codex_gpt_55"):
        factory.create("translator_codex_gpt_55")

    mismatched_codex = CurioConfig(
        llm_callers={
            "bad_codex": LlmCallerConfig(
                name="bad_codex",
                provider=ProviderName.CODEX_CLI,
                model="gpt-test",
                auth_config=OpenAiApiAuthConfig(),
                codex_exec_config=CodexCliExecConfig(),
                timeout_seconds=300,
            )
        }
    )
    with pytest.raises(LlmConfigurationError, match="codex_cli auth config is invalid"):
        LlmCallerFactory(
            config=mismatched_codex,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("bad_codex")

    missing_codex_exec = CurioConfig(
        llm_callers={
            "bad_codex": LlmCallerConfig(
                name="bad_codex",
                provider=ProviderName.CODEX_CLI,
                model="gpt-test",
                auth_config=CodexCliAuthConfig(),
                timeout_seconds=300,
            )
        }
    )
    with pytest.raises(LlmConfigurationError, match="codex_cli exec config is required"):
        LlmCallerFactory(
            config=missing_codex_exec,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("bad_codex")

    mismatched_openai = CurioConfig(
        llm_callers={
            "bad_openai": LlmCallerConfig(
                name="bad_openai",
                provider=ProviderName.OPENAI_API,
                model="gpt-test",
                auth_config=CodexCliAuthConfig(),
                timeout_seconds=300,
            )
        }
    )
    with pytest.raises(LlmConfigurationError, match="openai_api auth config is invalid"):
        LlmCallerFactory(
            config=mismatched_openai,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("bad_openai")

    mismatched_google = CurioConfig(
        llm_callers={
            "bad_google": LlmCallerConfig(
                name="bad_google",
                provider=ProviderName.GOOGLE_DOCUMENT_AI,
                model="gpt-test",
                auth_config=CodexCliAuthConfig(),
                timeout_seconds=300,
            )
        }
    )
    with pytest.raises(LlmConfigurationError, match="google_document_ai auth config is invalid"):
        LlmCallerFactory(
            config=mismatched_google,
            secret_store=make_secret_store(),
            codex_runner=FakeCodexRunner(),
            openai_transport=FakeOpenAiTransport(),
            codex_working_directory=tmp_path,
        ).create("bad_google")
