import hashlib
from pathlib import Path

from curio.llm_caller.models import (
    LlmRejectedRequestError,
    LlmRequest,
    LocalFileContentPart,
)


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_file_content_parts(request: LlmRequest) -> tuple[LocalFileContentPart, ...]:
    return tuple(
        part
        for message in request.input
        for part in message.content
        if isinstance(part, LocalFileContentPart)
    )


def single_local_file_content_part(
    request: LlmRequest,
    *,
    provider_name: str,
) -> LocalFileContentPart:
    local_files = local_file_content_parts(request)
    if len(local_files) != 1:
        raise LlmRejectedRequestError(f"{provider_name} requires exactly one local file input")
    return local_files[0]


def validate_local_file_content_part(
    part: LocalFileContentPart,
    *,
    provider_name: str,
    allowed_root: Path | None = None,
    allowed_root_description: str = "configured root",
) -> Path:
    try:
        resolved_path = Path(part.path).resolve(strict=True)
    except OSError as exc:
        raise LlmRejectedRequestError(f"{provider_name} local file is not readable: {part.path}") from exc
    if allowed_root is not None:
        try:
            resolved_path.relative_to(allowed_root.resolve())
        except ValueError as exc:
            raise LlmRejectedRequestError(
                f"{provider_name} local file must be under the {allowed_root_description}"
            ) from exc
    try:
        actual_sha256 = file_sha256(resolved_path)
    except OSError as exc:
        raise LlmRejectedRequestError(f"{provider_name} local file is not readable: {part.path}") from exc
    if actual_sha256 != part.sha256:
        raise LlmRejectedRequestError(f"{provider_name} local file sha256 did not match request metadata")
    return resolved_path


def read_local_file_content_part(
    part: LocalFileContentPart,
    *,
    provider_name: str,
    allowed_root: Path | None = None,
    allowed_root_description: str = "configured root",
) -> bytes:
    resolved_path = validate_local_file_content_part(
        part,
        provider_name=provider_name,
        allowed_root=allowed_root,
        allowed_root_description=allowed_root_description,
    )
    try:
        return resolved_path.read_bytes()
    except OSError as exc:
        raise LlmRejectedRequestError(f"{provider_name} local file is not readable: {part.path}") from exc
