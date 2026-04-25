import json
from pathlib import Path

import pytest

from curio.schemas import (
    DEFAULT_SCHEMA_DIR,
    SchemaLoadError,
    SchemaName,
    SchemaValidationError,
    load_schema,
    schema_path,
    validate_json,
)


def test_schema_path_resolves_known_schema() -> None:
    assert schema_path(SchemaName.LLM_REQUEST) == DEFAULT_SCHEMA_DIR / "llm_request.schema.json"
    assert schema_path("translation_response").name == "translation_response.schema.json"


def test_load_schema_loads_json_object() -> None:
    schema = load_schema(SchemaName.TRANSLATION_REQUEST)

    assert schema["title"] == "Curio Translation Request"


def test_load_schema_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SchemaLoadError, match="cannot load Curio schema"):
        load_schema(SchemaName.LLM_REQUEST, schema_dir=tmp_path)


def test_load_schema_rejects_non_object_schema(tmp_path: Path) -> None:
    path = tmp_path / "llm_request.schema.json"
    path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(SchemaLoadError, match="not a JSON object"):
        load_schema(SchemaName.LLM_REQUEST, schema_dir=tmp_path)


def test_validate_json_accepts_valid_payload() -> None:
    payload = {
        "translation_request_version": "curio-translation-request.v1",
        "request_id": "translate-test",
        "target_language": "en",
        "english_confidence_threshold": 0.9,
        "blocks": [
            {
                "block_id": 1,
                "name": "tweet_text",
                "source_language_hint": None,
                "text": "bonjour",
            }
        ],
    }

    validate_json(payload, SchemaName.TRANSLATION_REQUEST)


def test_validate_json_rejects_invalid_payload() -> None:
    with pytest.raises(SchemaValidationError, match="translation_request"):
        validate_json({"request_id": ""}, SchemaName.TRANSLATION_REQUEST)


def test_validate_json_rejects_auth_capability_in_llm_request() -> None:
    payload = {
        "llm_request_version": "curio-llm-request.v1",
        "request_id": "translate-test",
        "workflow": "translate",
        "model": None,
        "instructions": "Return JSON.",
        "input": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Translate this."}],
            }
        ],
        "output": {
            "type": "json_schema",
            "name": "output",
            "schema": {},
            "strict": True,
        },
        "required_capabilities": ["chatgpt_auth"],
        "timeout_seconds": 300,
        "metadata": {},
    }

    with pytest.raises(SchemaValidationError, match="chatgpt_auth"):
        validate_json(payload, SchemaName.LLM_REQUEST)
