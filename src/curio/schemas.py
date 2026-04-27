import json
from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as JsonSchemaLibraryError

JsonObject = dict[str, Any]

DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


class SchemaName(StrEnum):
    EVALUATION_PAYLOAD = "evaluation_payload"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TEXTIFY_REQUEST = "textify_request"
    TEXTIFY_RESPONSE = "textify_response"
    TRANSLATION_REQUEST = "translation_request"
    TRANSLATION_RESPONSE = "translation_response"


_SCHEMA_FILENAMES = {
    SchemaName.EVALUATION_PAYLOAD: "evaluation_payload.schema.json",
    SchemaName.LLM_REQUEST: "llm_request.schema.json",
    SchemaName.LLM_RESPONSE: "llm_response.schema.json",
    SchemaName.TEXTIFY_REQUEST: "textify_request.schema.json",
    SchemaName.TEXTIFY_RESPONSE: "textify_response.schema.json",
    SchemaName.TRANSLATION_REQUEST: "translation_request.schema.json",
    SchemaName.TRANSLATION_RESPONSE: "translation_response.schema.json",
}


class CurioSchemaError(ValueError):
    pass


class SchemaLoadError(CurioSchemaError):
    pass


class SchemaValidationError(CurioSchemaError):
    pass


def schema_path(name: SchemaName | str, schema_dir: Path | None = None) -> Path:
    schema_name = SchemaName(name)
    return (schema_dir or DEFAULT_SCHEMA_DIR) / _SCHEMA_FILENAMES[schema_name]


def load_schema(name: SchemaName | str, schema_dir: Path | None = None) -> JsonObject:
    path = schema_path(name, schema_dir)
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, JSONDecodeError) as exc:
        raise SchemaLoadError(f"cannot load Curio schema at {path}") from exc
    if not isinstance(schema, dict):
        raise SchemaLoadError(f"Curio schema at {path} is not a JSON object")
    return schema


def validate_json(
    value: Any,
    schema_name: SchemaName | str,
    schema_dir: Path | None = None,
) -> None:
    resolved_schema_name = SchemaName(schema_name)
    validator = Draft202012Validator(
        load_schema(resolved_schema_name, schema_dir),
        format_checker=FormatChecker(),
    )
    try:
        validator.validate(value)
    except JsonSchemaLibraryError as exc:
        raise SchemaValidationError(f"{resolved_schema_name.value}: {exc.message}") from exc
