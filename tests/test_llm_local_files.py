from pathlib import Path

import pytest

import curio.llm_caller.local_files as local_files
from curio.llm_caller import (
    JsonSchemaOutput,
    LlmMessage,
    LlmRejectedRequestError,
    LlmRequest,
    LocalFileContentPart,
    TextContentPart,
    file_sha256,
    local_file_content_parts,
    read_local_file_content_part,
    single_local_file_content_part,
    validate_local_file_content_part,
)


def make_file_part(path: Path, *, sha256: str | None = None) -> LocalFileContentPart:
    return LocalFileContentPart(
        path=str(path.resolve()),
        mime_type="image/png",
        sha256=file_sha256(path) if sha256 is None else sha256,
        name=path.name,
    )


def make_request(*parts: LocalFileContentPart) -> LlmRequest:
    return LlmRequest(
        request_id="local-file-test",
        workflow="textify",
        instructions="Extract text.",
        input=[
            LlmMessage(
                role="user",
                content=[TextContentPart("see files"), *parts],
            )
        ],
        output=JsonSchemaOutput(name="output", schema={"type": "object"}),
    )


def test_local_file_content_parts_extracts_all_parts(tmp_path: Path) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    first_path.write_bytes(b"first")
    second_path.write_bytes(b"second")
    first = make_file_part(first_path)
    second = make_file_part(second_path)

    request = make_request(first, second)

    assert local_file_content_parts(request) == (first, second)


def test_single_local_file_content_part_requires_exactly_one(tmp_path: Path) -> None:
    path = tmp_path / "scan.png"
    path.write_bytes(b"scan")
    part = make_file_part(path)

    assert single_local_file_content_part(make_request(part), provider_name="provider_test") == part

    with pytest.raises(LlmRejectedRequestError, match="provider_test requires exactly one local file"):
        single_local_file_content_part(make_request(), provider_name="provider_test")

    with pytest.raises(LlmRejectedRequestError, match="provider_test requires exactly one local file"):
        single_local_file_content_part(make_request(part, part), provider_name="provider_test")


def test_validate_local_file_content_part_checks_sha_and_allowed_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    inside = root / "scan.png"
    inside.write_bytes(b"inside")
    part = make_file_part(inside)

    assert validate_local_file_content_part(part, provider_name="provider_test", allowed_root=root) == inside.resolve()
    assert read_local_file_content_part(part, provider_name="provider_test", allowed_root=root) == b"inside"

    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    outside_part = make_file_part(outside)
    with pytest.raises(LlmRejectedRequestError, match="configured root"):
        validate_local_file_content_part(outside_part, provider_name="provider_test", allowed_root=root)

    bad_sha_part = make_file_part(inside, sha256="bad-sha")
    with pytest.raises(LlmRejectedRequestError, match="sha256"):
        validate_local_file_content_part(bad_sha_part, provider_name="provider_test", allowed_root=root)

    missing_part = LocalFileContentPart(
        path=str((root / "missing.png").resolve()),
        mime_type="image/png",
        sha256="abc",
    )
    with pytest.raises(LlmRejectedRequestError, match="not readable"):
        validate_local_file_content_part(missing_part, provider_name="provider_test", allowed_root=root)


def test_validate_local_file_content_part_reports_late_read_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "scan.png"
    path.write_bytes(b"scan")
    part = make_file_part(path)

    def raise_os_error(path: str | Path) -> str:
        del path
        raise OSError("late hash failure")

    monkeypatch.setattr(local_files, "file_sha256", raise_os_error)

    with pytest.raises(LlmRejectedRequestError, match="not readable"):
        validate_local_file_content_part(part, provider_name="provider_test")


def test_read_local_file_content_part_reports_late_read_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "scan.png"
    path.write_bytes(b"scan")
    part = make_file_part(path)

    monkeypatch.setattr(local_files, "validate_local_file_content_part", lambda *args, **kwargs: tmp_path / "missing.png")

    with pytest.raises(LlmRejectedRequestError, match="not readable"):
        read_local_file_content_part(part, provider_name="provider_test")
