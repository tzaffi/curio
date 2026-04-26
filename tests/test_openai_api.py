import json
from collections.abc import Mapping
from typing import cast

import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError

import curio.llm_caller.openai_api as openai_api
from curio.llm_caller import (
    OPENAI_API_CAPABILITIES,
    InMemorySecretStore,
    JsonSchemaOutput,
    LlmAuthError,
    LlmCapability,
    LlmInvalidOutputError,
    LlmMessage,
    LlmRejectedRequestError,
    LlmRequest,
    LlmSchemaValidationError,
    LlmTimeoutError,
    OpenAiApiAuthConfig,
    OpenAiApiCallResult,
    OpenAiApiClient,
    OpenAiReasoningEffort,
    OpenAiResponsesConfig,
    OpenAiTextVerbosity,
    ProviderCallTiming,
    ProviderName,
    SdkOpenAiApiTransport,
    SecretRef,
    TextContentPart,
    UnsupportedCapabilityError,
    build_openai_llm_response,
    build_openai_response_request,
    parse_openai_response_output,
)


def make_secret_ref() -> SecretRef:
    return SecretRef(service="curio/openai-api", account="default-api-key")


def make_secret_store(secret: str = "sk-test-secret") -> InMemorySecretStore:
    store = InMemorySecretStore()
    store.set_secret(make_secret_ref(), secret)
    return store


def make_auth_config() -> OpenAiApiAuthConfig:
    return OpenAiApiAuthConfig(api_key_ref=make_secret_ref(), organization="org-test", project="proj-test")


def make_request(
    *,
    required_capabilities: list[LlmCapability | str] | None = None,
    output_schema: dict[str, object] | None = None,
) -> LlmRequest:
    return LlmRequest(
        request_id="translate-test",
        workflow="translate",
        instructions="Return translated blocks as JSON.",
        input=[
            LlmMessage(role="system", content=[TextContentPart(text="System context.")]),
            LlmMessage(role="user", content=[TextContentPart(text="Bonjour."), TextContentPart(text="Salut.")]),
        ],
        output=JsonSchemaOutput(
            name="curio_translation_model_output",
            schema={"type": "object"} if output_schema is None else output_schema,
        ),
        required_capabilities=["text_generation", "json_schema_output"]
        if required_capabilities is None
        else required_capabilities,
        metadata={},
    )


def make_timing() -> ProviderCallTiming:
    return ProviderCallTiming(
        started_at="2026-04-24T15:20:00Z",
        completed_at="2026-04-24T15:20:03Z",
        wall_seconds=3,
    )


def make_response_payload(
    output_text: str = "{}",
    *,
    status: str = "completed",
    model: object = "gpt-test",
    usage: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "id": "resp_test",
        "status": status,
        "model": model,
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": output_text}],
            }
        ],
        "usage": {
            "input_tokens": 20,
            "input_tokens_details": {"cached_tokens": 5},
            "output_tokens": 7,
            "output_tokens_details": {"reasoning_tokens": 2},
            "total_tokens": 27,
        }
        if usage is None
        else usage,
    }


class FakeOpenAiTransport:
    def __init__(
        self,
        payload: Mapping[str, object] | None = None,
        *,
        exception: Exception | None = None,
    ) -> None:
        self.payload = make_response_payload() if payload is None else dict(payload)
        self.exception = exception
        self.calls: list[tuple[Mapping[str, object], str, OpenAiApiAuthConfig, int]] = []

    def create_response(
        self,
        request_payload: Mapping[str, object],
        *,
        api_key: str,
        auth_config: OpenAiApiAuthConfig,
        timeout_seconds: int,
    ) -> OpenAiApiCallResult:
        self.calls.append((dict(request_payload), api_key, auth_config, timeout_seconds))
        if self.exception is not None:
            raise self.exception
        return OpenAiApiCallResult(payload=self.payload, timing=make_timing())


def make_client(
    transport: FakeOpenAiTransport,
    *,
    model: str = "gpt-test",
    timeout_seconds: int = 120,
    responses_config: OpenAiResponsesConfig | None = None,
) -> OpenAiApiClient:
    return OpenAiApiClient(
        transport=transport,
        auth_config=make_auth_config(),
        secret_store=make_secret_store(),
        model=model,
        timeout_seconds=timeout_seconds,
        responses_config=responses_config,
    )


def test_build_openai_response_request_maps_llm_request_without_secret() -> None:
    responses_config = OpenAiResponsesConfig(
        temperature=0,
        reasoning_effort=OpenAiReasoningEffort.LOW,
        max_output_tokens=2000,
        text_verbosity="low",
    )
    payload = build_openai_response_request(
        make_request(),
        model="gpt-test",
        responses_config=responses_config,
    )

    assert responses_config.reasoning_effort == OpenAiReasoningEffort.LOW
    assert responses_config.text_verbosity == OpenAiTextVerbosity.LOW
    assert payload == {
        "model": "gpt-test",
        "instructions": "Return translated blocks as JSON.",
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": "System context."}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Bonjour."},
                    {"type": "input_text", "text": "Salut."},
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "curio_translation_model_output",
                "schema": {"type": "object"},
                "strict": True,
            },
            "verbosity": "low",
        },
        "metadata": {
            "curio_request_id": "translate-test",
            "curio_workflow": "translate",
        },
        "temperature": 0,
        "max_output_tokens": 2000,
        "reasoning": {"effort": "low"},
    }
    assert "sk-test-secret" not in str(payload)


def test_build_openai_response_request_omits_empty_tuning_values() -> None:
    payload = build_openai_response_request(make_request(), model="gpt-test", responses_config=OpenAiResponsesConfig())

    assert payload["text"] == {
        "format": {
            "type": "json_schema",
            "name": "curio_translation_model_output",
            "schema": {"type": "object"},
            "strict": True,
        }
    }
    assert "temperature" not in payload
    assert "max_output_tokens" not in payload
    assert "reasoning" not in payload


def test_openai_responses_config_rejects_invalid_tuning_values() -> None:
    with pytest.raises(ValueError, match="temperature must be a number between 0 and 2"):
        OpenAiResponsesConfig(temperature=True)

    with pytest.raises(ValueError, match="temperature must be a number between 0 and 2"):
        OpenAiResponsesConfig(temperature=3)

    with pytest.raises(ValueError, match="reasoning_effort must be one of"):
        OpenAiResponsesConfig(reasoning_effort="turbo")

    with pytest.raises(ValueError, match="max_output_tokens must be a positive integer"):
        OpenAiResponsesConfig(max_output_tokens=0)

    with pytest.raises(ValueError, match="max_output_tokens must be a positive integer"):
        OpenAiResponsesConfig(max_output_tokens=False)

    with pytest.raises(ValueError, match="text_verbosity must be one of"):
        OpenAiResponsesConfig(text_verbosity="verbose")

    with pytest.raises(ValueError, match="model must be a string"):
        build_openai_response_request(make_request(), model=cast(str, None))

    with pytest.raises(ValueError, match="model must not be empty"):
        build_openai_response_request(make_request(), model=" ")


def test_parse_openai_response_output_and_usage_mapping() -> None:
    payload = make_response_payload(json.dumps({"ok": True}))
    output_value = parse_openai_response_output(payload)
    response = build_openai_llm_response(
        make_request(),
        payload,
        make_timing(),
        model="gpt-test",
        output_value=output_value,
    )

    assert output_value == {"ok": True}
    assert response.provider == ProviderName.OPENAI_API
    assert response.model == "gpt-test"
    assert response.output is not None
    assert response.output.value == {"ok": True}
    assert response.usage.input_tokens == 20
    assert response.usage.cached_input_tokens == 5
    assert response.usage.output_tokens == 7
    assert response.usage.reasoning_tokens == 2
    assert response.usage.total_tokens == 27
    assert response.usage.thinking_seconds is None


def test_openai_api_client_calls_fake_transport_and_resolves_secret_at_call_time(capsys: pytest.CaptureFixture[str]) -> None:
    secret = "sk-test-secret"
    transport = FakeOpenAiTransport(make_response_payload(json.dumps({"ok": True})))
    client = OpenAiApiClient(
        transport=transport,
        auth_config=make_auth_config(),
        secret_store=make_secret_store(secret),
        model="gpt-test",
        timeout_seconds=120,
    )

    response = client.complete(
        make_request(
            output_schema={
                "type": "object",
                "required": ["ok"],
                "properties": {"ok": {"type": "boolean"}},
                "additionalProperties": False,
            }
        )
    )

    request_payload, api_key, auth_config, timeout_seconds = transport.calls[0]
    print(request_payload)
    captured = capsys.readouterr()
    assert api_key == secret
    assert auth_config == make_auth_config()
    assert timeout_seconds == 120
    assert secret not in str(request_payload)
    assert secret not in captured.out
    assert secret not in captured.err
    assert response.output is not None
    assert response.output.value == {"ok": True}


def test_openai_api_client_uses_explicit_dependencies_and_named_config_values() -> None:
    transport = FakeOpenAiTransport()
    auth_config = make_auth_config()
    secret_store = make_secret_store()
    responses_config = OpenAiResponsesConfig(temperature=0.5)
    client = OpenAiApiClient(
        transport=transport,
        auth_config=auth_config,
        secret_store=secret_store,
        model="gpt-configured",
        timeout_seconds=90,
        responses_config=responses_config,
    )

    assert client.transport is transport
    assert client.auth_config is auth_config
    assert client.secret_store is secret_store
    assert client.capabilities == OPENAI_API_CAPABILITIES
    assert client.provider == ProviderName.OPENAI_API
    assert client.model == "gpt-configured"
    assert client.timeout_seconds == 90
    assert client.responses_config is responses_config


def test_openai_api_client_uses_configured_model_for_fake_transport() -> None:
    transport = FakeOpenAiTransport(make_response_payload(json.dumps({})))
    client = make_client(transport, model="gpt-configured")

    response = client.complete(make_request())

    request_payload, _, _, _ = transport.calls[0]
    assert request_payload["model"] == "gpt-configured"
    assert response.model == "gpt-test"


def test_openai_api_client_rejects_unsupported_capability_before_secret_lookup() -> None:
    transport = FakeOpenAiTransport()
    client = make_client(transport)

    with pytest.raises(UnsupportedCapabilityError, match="thinking_time"):
        client.complete(make_request(required_capabilities=["thinking_time"]))

    assert transport.calls == []


def test_openai_api_client_maps_transport_timeout() -> None:
    client = make_client(FakeOpenAiTransport(exception=TimeoutError("secret timeout detail")))

    with pytest.raises(LlmTimeoutError) as exc:
        client.complete(make_request())

    assert str(exc.value) == "openai_api request timed out"
    assert "secret" not in str(exc.value)


def test_openai_api_client_reports_invalid_or_schema_invalid_output() -> None:
    invalid_json = make_client(FakeOpenAiTransport(make_response_payload("not json")))
    with pytest.raises(LlmInvalidOutputError, match="output_text is not valid JSON"):
        invalid_json.complete(make_request())

    schema_invalid = make_client(FakeOpenAiTransport(make_response_payload(json.dumps({"ok": "yes"}))))
    with pytest.raises(LlmSchemaValidationError, match="output did not match requested schema"):
        schema_invalid.complete(
            make_request(
                output_schema={
                    "type": "object",
                    "required": ["ok"],
                    "properties": {"ok": {"type": "boolean"}},
                }
            )
        )


def test_parse_openai_response_output_reports_invalid_response_shapes() -> None:
    with pytest.raises(LlmInvalidOutputError, match="response must be an object"):
        parse_openai_response_output([])

    with pytest.raises(LlmRejectedRequestError, match="response was not completed"):
        parse_openai_response_output(make_response_payload(status="failed"))

    with pytest.raises(LlmInvalidOutputError, match="output must be a list"):
        parse_openai_response_output({"status": "completed", "output": {}})

    with pytest.raises(LlmInvalidOutputError, match="output item must be an object"):
        parse_openai_response_output({"status": "completed", "output": ["bad"]})

    with pytest.raises(LlmInvalidOutputError, match="content must be a list"):
        parse_openai_response_output({"status": "completed", "output": [{"type": "message", "content": {}}]})

    with pytest.raises(LlmInvalidOutputError, match="content item must be an object"):
        parse_openai_response_output({"status": "completed", "output": [{"type": "message", "content": ["bad"]}]})

    with pytest.raises(LlmInvalidOutputError, match="output text must be a string"):
        parse_openai_response_output(
            {
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": 1}]}],
            }
        )

    with pytest.raises(LlmInvalidOutputError, match="output text must not be empty"):
        parse_openai_response_output(
            {
                "status": "completed",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": " "}]}],
            }
        )

    with pytest.raises(LlmInvalidOutputError, match="did not include output_text"):
        parse_openai_response_output({"status": "completed", "output": [{"type": "tool_call"}]})


def test_build_openai_llm_response_handles_missing_usage_and_configured_model_fallback() -> None:
    payload = make_response_payload(json.dumps({}), model=None, usage={})
    output_value = parse_openai_response_output(payload)

    response = build_openai_llm_response(
        make_request(),
        payload,
        make_timing(),
        model="gpt-configured",
        output_value=output_value,
    )

    assert response.model == "gpt-configured"
    assert response.usage.input_tokens is None
    assert response.usage.cached_input_tokens is None
    assert response.usage.output_tokens is None
    assert response.usage.reasoning_tokens is None
    assert response.usage.total_tokens is None


def test_build_openai_llm_response_handles_absent_usage_and_nested_details() -> None:
    no_usage_payload = {
        "status": "completed",
        "model": "gpt-test",
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}],
    }
    output_value = parse_openai_response_output(no_usage_payload)
    no_usage = build_openai_llm_response(
        make_request(),
        no_usage_payload,
        make_timing(),
        model="gpt-configured",
        output_value=output_value,
    )

    assert no_usage.usage.input_tokens is None
    assert no_usage.usage.cached_input_tokens is None
    assert no_usage.usage.reasoning_tokens is None

    sparse_usage_payload = make_response_payload(usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3})
    sparse_usage = build_openai_llm_response(
        make_request(),
        sparse_usage_payload,
        make_timing(),
        model="gpt-configured",
        output_value={},
    )

    assert sparse_usage.usage.input_tokens == 1
    assert sparse_usage.usage.cached_input_tokens is None
    assert sparse_usage.usage.reasoning_tokens is None


def test_build_openai_llm_response_reports_invalid_usage_and_model_shapes() -> None:
    with pytest.raises(LlmInvalidOutputError, match="input_tokens must be a non-negative number"):
        build_openai_llm_response(
            make_request(),
            make_response_payload(usage={"input_tokens": -1}),
            make_timing(),
            model="gpt-test",
            output_value={},
        )

    with pytest.raises(LlmInvalidOutputError, match="output_tokens must be a non-negative number"):
        build_openai_llm_response(
            make_request(),
            make_response_payload(usage={"output_tokens": True}),
            make_timing(),
            model="gpt-test",
            output_value={},
        )

    with pytest.raises(LlmInvalidOutputError, match="field must be an object"):
        build_openai_llm_response(
            make_request(),
            make_response_payload(usage={"input_tokens_details": "bad"}),
            make_timing(),
            model="gpt-test",
            output_value={},
        )

    with pytest.raises(LlmInvalidOutputError, match="string field must be a string"):
        build_openai_llm_response(
            make_request(),
            make_response_payload(model=1),
            make_timing(),
            model="gpt-test",
            output_value={},
        )


def test_openai_api_call_result_rejects_invalid_payload() -> None:
    with pytest.raises(LlmInvalidOutputError, match="payload must be an object"):
        OpenAiApiCallResult(payload=cast(Mapping[str, object], []), timing=make_timing())


class ModelDumpResponse:
    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return make_response_payload(json.dumps({"ok": True}))


class ToDictResponse:
    def to_dict(self) -> dict[str, object]:
        return make_response_payload(json.dumps({"ok": True}))


class BadResponse:
    pass


class FakeResponses:
    def __init__(self, response: object | None = None, exception: Exception | None = None) -> None:
        self.response = ModelDumpResponse() if response is None else response
        self.exception = exception
        self.calls: list[Mapping[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.exception is not None:
            raise self.exception
        return self.response


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []
    next_response: object | None = None
    next_exception: Exception | None = None

    def __init__(
        self,
        *,
        api_key: str,
        organization: str | None,
        project: str | None,
        timeout: int,
        max_retries: int,
    ) -> None:
        self.api_key = api_key
        self.organization = organization
        self.project = project
        self.timeout = timeout
        self.max_retries = max_retries
        self.responses = FakeResponses(self.next_response, self.next_exception)
        self.instances.append(self)


def test_sdk_transport_maps_request_and_serializes_model_dump_response(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeOpenAI.instances = []
    FakeOpenAI.next_response = ModelDumpResponse()
    FakeOpenAI.next_exception = None
    monkeypatch.setattr(openai_api, "OpenAI", FakeOpenAI)

    result = SdkOpenAiApiTransport().create_response(
        {"model": "gpt-test"},
        api_key="sk-test-secret",
        auth_config=make_auth_config(),
        timeout_seconds=120,
    )

    instance = FakeOpenAI.instances[0]
    assert instance.api_key == "sk-test-secret"
    assert instance.organization == "org-test"
    assert instance.project == "proj-test"
    assert instance.timeout == 120
    assert instance.max_retries == 0
    assert instance.responses.calls == [{"model": "gpt-test", "timeout": 120}]
    assert parse_openai_response_output(result.payload) == {"ok": True}
    assert result.timing.wall_seconds >= 0


def test_sdk_transport_accepts_mapping_response(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeOpenAI.instances = []
    FakeOpenAI.next_response = make_response_payload(json.dumps({"ok": True}))
    FakeOpenAI.next_exception = None
    monkeypatch.setattr(openai_api, "OpenAI", FakeOpenAI)

    result = SdkOpenAiApiTransport().create_response(
        {"model": "gpt-test"},
        api_key="sk-test-secret",
        auth_config=make_auth_config(),
        timeout_seconds=120,
    )

    assert parse_openai_response_output(result.payload) == {"ok": True}


def test_sdk_transport_serializes_to_dict_response(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeOpenAI.instances = []
    FakeOpenAI.next_response = ToDictResponse()
    FakeOpenAI.next_exception = None
    monkeypatch.setattr(openai_api, "OpenAI", FakeOpenAI)

    result = SdkOpenAiApiTransport().create_response(
        {"model": "gpt-test"},
        api_key="sk-test-secret",
        auth_config=make_auth_config(),
        timeout_seconds=120,
    )

    assert parse_openai_response_output(result.payload) == {"ok": True}


def test_sdk_transport_rejects_unserializable_response(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeOpenAI.instances = []
    FakeOpenAI.next_response = BadResponse()
    FakeOpenAI.next_exception = None
    monkeypatch.setattr(openai_api, "OpenAI", FakeOpenAI)

    with pytest.raises(LlmInvalidOutputError, match="SDK response is not serializable"):
        SdkOpenAiApiTransport().create_response(
            {"model": "gpt-test"},
            api_key="sk-test-secret",
            auth_config=make_auth_config(),
            timeout_seconds=120,
        )


def test_sdk_transport_maps_openai_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response_401 = httpx.Response(401, request=request)
    response_500 = httpx.Response(500, request=request)
    cases = [
        (APITimeoutError(request), LlmTimeoutError, "openai_api request timed out"),
        (
            APIConnectionError(message="contains sk-test-secret", request=request),
            LlmRejectedRequestError,
            "openai_api connection failed",
        ),
        (
            APIStatusError("contains sk-test-secret", response=response_401, body=None),
            LlmAuthError,
            "openai_api authentication failed",
        ),
        (
            APIStatusError("contains sk-test-secret", response=response_500, body=None),
            LlmRejectedRequestError,
            "openai_api request failed",
        ),
        (OpenAIError("contains sk-test-secret"), LlmRejectedRequestError, "openai_api request failed"),
    ]

    for exception, expected_type, expected_message in cases:
        FakeOpenAI.instances = []
        FakeOpenAI.next_response = None
        FakeOpenAI.next_exception = exception
        monkeypatch.setattr(openai_api, "OpenAI", FakeOpenAI)

        with pytest.raises(expected_type) as exc:
            SdkOpenAiApiTransport().create_response(
                {"model": "gpt-test"},
                api_key="sk-test-secret",
                auth_config=make_auth_config(),
                timeout_seconds=120,
            )

        assert str(exc.value) == expected_message
        assert "sk-test-secret" not in str(exc.value)
