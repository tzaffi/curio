from pathlib import Path

import pytest

from curio.config import LlmCallerPromptConfig
from curio.llm_caller import LlmCapability, LocalFileContentPart, TextContentPart
from curio.schemas import SchemaName, validate_json
from curio.textify import Artifact, TextifyRequest, file_sha256
from curio.textify.adapter import (
    DEFAULT_TEXTIFY_INSTRUCTIONS,
    DEFAULT_TEXTIFY_USER_PROMPT_TEMPLATE,
    SUGGESTED_FILE_POLICY,
    TEXTIFY_MODEL_OUTPUT_SCHEMA_NAME,
    TEXTIFY_WORKFLOW,
    artifact_manifest,
    build_textify_instructions,
    build_textify_llm_request,
    build_textify_prompt,
    build_textify_template_values,
    textify_model_output_schema,
)


def make_artifact(path: Path, *, mime_type: str = "image/png") -> Artifact:
    path.write_bytes(b"media bytes")
    return Artifact(
        artifact_id=3,
        name=path.name,
        path=str(path),
        mime_type=mime_type,
        sha256=file_sha256(path),
        source_language_hint="ja",
        context={"artifact_kind": "image"},
    )


def test_textify_model_output_schema_and_prompt_values(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", artifacts=[artifact], llm_caller="textifier")

    schema = textify_model_output_schema()
    values = build_textify_template_values(request, artifact)

    assert schema["$defs"]["modelArtifact"]["properties"]["status"]["enum"] == ["converted", "no_text_found"]
    assert values["request_id"] == "textify-test"
    assert values["preferred_output_format"] == "markdown"
    assert SUGGESTED_FILE_POLICY in build_textify_prompt(request, artifact)
    assert "Do not translate" in build_textify_prompt(request, artifact)
    assert "Return only JSON" in build_textify_instructions(request, artifact)
    assert DEFAULT_TEXTIFY_INSTRUCTIONS.startswith("Return only JSON")
    assert "{textify_request_json}" in DEFAULT_TEXTIFY_USER_PROMPT_TEMPLATE


def test_textify_prompt_overrides_are_applied(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png")
    request = TextifyRequest(request_id="textify-test", artifacts=[artifact])
    prompt_config = LlmCallerPromptConfig(
        instructions="Instructions {request_id} {preferred_output_format}",
        user="User {artifact_manifest_json} {output_schema_json}",
    )

    assert build_textify_instructions(request, artifact, prompt_config) == "Instructions textify-test markdown"
    assert '"artifact_id": 3' in build_textify_prompt(request, artifact, prompt_config)
    assert '"modelArtifact"' in build_textify_prompt(request, artifact, prompt_config)


def test_build_textify_llm_request_includes_file_part_and_capabilities(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.pdf", mime_type="application/pdf")
    request = TextifyRequest(request_id="textify-test", artifacts=[artifact], preferred_output_format="txt")

    llm_request = build_textify_llm_request(request, artifact)
    text_part, file_part = llm_request.input[0].content

    assert llm_request.workflow == TEXTIFY_WORKFLOW
    assert llm_request.output.name == TEXTIFY_MODEL_OUTPUT_SCHEMA_NAME
    assert LlmCapability.FILE_INPUT in llm_request.required_capabilities
    assert LlmCapability.PDF_INPUT in llm_request.required_capabilities
    assert LlmCapability.IMAGE_INPUT not in llm_request.required_capabilities
    assert isinstance(text_part, TextContentPart)
    assert isinstance(file_part, LocalFileContentPart)
    assert file_part.path == artifact.path
    assert llm_request.metadata["suggested_path"] == "scan.txt"
    validate_json(llm_request.to_json(), SchemaName.LLM_REQUEST)


def test_textify_artifact_manifest_uses_effective_metadata(tmp_path: Path) -> None:
    artifact = make_artifact(tmp_path / "scan.png", mime_type="IMAGE/PNG")

    manifest = artifact_manifest(artifact, "markdown")

    assert manifest["mime_type"] == "image/png"
    assert manifest["sha256"] == file_sha256(tmp_path / "scan.png")
    assert manifest["preferred_output_format"] == "markdown"


def test_build_textify_llm_request_rejects_missing_file_for_sha(tmp_path: Path) -> None:
    artifact = Artifact(artifact_id=1, name="missing.png", path=str(tmp_path / "missing.png"), mime_type="image/png")
    request = TextifyRequest(request_id="textify-test", artifacts=[artifact])

    with pytest.raises(FileNotFoundError):
        build_textify_llm_request(request, artifact)
