import mimetypes
from pathlib import Path

from curio.llm_caller.local_files import file_sha256 as llm_file_sha256
from curio.textify.models import Artifact, PreferredOutputFormat

TEXT_MIME_TYPES = frozenset(
    (
        "application/json",
        "application/ld+json",
        "application/toml",
        "application/xml",
        "application/x-yaml",
        "text/csv",
        "text/html",
        "text/markdown",
        "text/plain",
        "text/tab-separated-values",
        "text/x-python",
        "text/x-shellscript",
    )
)
TEXT_EXTENSIONS = frozenset(
    (
        ".csv",
        ".html",
        ".htm",
        ".json",
        ".log",
        ".md",
        ".py",
        ".rst",
        ".sh",
        ".toml",
        ".tsv",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    )
)
IMAGE_MIME_TYPES = frozenset(
    (
        "image/bmp",
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    )
)
IMAGE_EXTENSIONS = frozenset((".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"))
DOCUMENT_MIME_TYPES = frozenset(
    (
        "application/pdf",
        "application/vnd.ms-excel.sheet.macroenabled.12",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
    )
)
DOCUMENT_EXTENSIONS = frozenset((".docx", ".html", ".pdf", ".pptx", ".xlsm", ".xlsx"))


def normalize_mime_type(mime_type: str | None) -> str | None:
    if mime_type is None:
        return None
    media_type = mime_type.split(";", 1)[0].strip().casefold()
    return media_type or None


def mime_type_for_path(path: str | Path) -> str | None:
    guessed, _encoding = mimetypes.guess_type(str(path))
    return normalize_mime_type(guessed)


def effective_mime_type(artifact: Artifact) -> str | None:
    return normalize_mime_type(artifact.mime_type) or mime_type_for_path(artifact.path)


def file_sha256(path: str | Path) -> str:
    return llm_file_sha256(path)


def is_deterministic_text_media(artifact: Artifact) -> bool:
    mime_type = effective_mime_type(artifact)
    suffix = Path(artifact.path).suffix.casefold()
    if mime_type is not None and (mime_type.startswith("text/") or mime_type in TEXT_MIME_TYPES):
        return True
    if suffix in TEXT_EXTENSIONS:
        return is_probably_plaintext(Path(artifact.path))
    return False


def is_probably_plaintext(path: Path, *, sample_size: int = 8192) -> bool:
    try:
        sample = path.read_bytes()[:sample_size]
    except OSError:
        return False
    if not sample:
        return True
    if b"\x00" in sample:
        return False
    for bom in (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff"):
        if sample.startswith(bom):
            sample = sample[len(bom) :]
            break
    try:
        decoded = sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if not decoded:
        return True
    control_count = sum(1 for char in decoded if ord(char) < 32 and char not in "\n\r\t\f\b")
    return control_count / len(decoded) <= 0.01


def is_provider_supported_media(artifact: Artifact) -> bool:
    mime_type = effective_mime_type(artifact)
    suffix = Path(artifact.path).suffix.casefold()
    return (
        mime_type in IMAGE_MIME_TYPES
        or mime_type in DOCUMENT_MIME_TYPES
        or suffix in IMAGE_EXTENSIONS
        or suffix in DOCUMENT_EXTENSIONS
    )


def preferred_output_hint(artifact: Artifact, request_preference: PreferredOutputFormat | str) -> str:
    preference = PreferredOutputFormat(request_preference)
    if preference != PreferredOutputFormat.AUTO:
        return preference.value
    suffix = Path(artifact.path).suffix.casefold()
    if suffix in {".log", ".txt"}:
        return PreferredOutputFormat.TXT.value
    return PreferredOutputFormat.MARKDOWN.value


def source_sha256(artifact: Artifact) -> str:
    return artifact.sha256 or file_sha256(artifact.path)
