import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import uuid4

from curio.config import GoogleConfig, PipelineConfig
from curio.google_api import (
    GOOGLE_PIPELINE_SCOPES,
    GoogleSession,
    build_authorized_session,
    raise_for_status,
)
from curio.pipeline.local import LocalArtifactStore
from curio.pipeline.models import ArtifactRef, ProcessCandidate, ProcessorObject

GOOGLE_DRIVE_API_BASE_URL = "https://www.googleapis.com/drive/v3"
GOOGLE_DRIVE_UPLOAD_API_BASE_URL = "https://www.googleapis.com/upload/drive/v3"
GOOGLE_DRIVE_FILE_FIELDS = "id,name,mimeType,webViewLink,parents,appProperties,size"
GOOGLE_DRIVE_FOLDER_FIELDS = "id,name,mimeType,trashed"
GOOGLE_DRIVE_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
CURIO_SHA256_PROPERTY = "curio_sha256"


@dataclass(frozen=True, slots=True)
class DriveFile:
    id: str
    name: str
    mime_type: str
    web_view_link: str
    parents: tuple[str, ...]
    app_properties: Mapping[str, str]
    size_bytes: int | None = None


@dataclass(frozen=True, slots=True)
class DriveFolder:
    id: str
    name: str
    mime_type: str
    trashed: bool


class GoogleDriveArtifactStore:
    def __init__(self, *, root: Path, config: PipelineConfig, client: "GoogleDriveClient") -> None:
        self.root = root
        self.config = config
        self.client = client
        self._local_store = LocalArtifactStore(root)
        self._created_drive_files_by_url: dict[str, str] = {}

    @classmethod
    def from_config(cls, *, google_config: GoogleConfig, pipeline_config: PipelineConfig) -> "GoogleDriveArtifactStore":
        _validate_local_artifact_directories(pipeline_config)
        session = build_authorized_session(google_config, scopes=GOOGLE_PIPELINE_SCOPES)
        store = cls(
            root=pipeline_config.effective_artifact_root,
            config=pipeline_config,
            client=GoogleDriveClient(session),
        )
        store.validate_configured_folders()
        return store

    def validate_configured_folders(self) -> None:
        self.client.get_folder(self.config.drive_folders.textifications)
        self.client.get_folder(self.config.drive_folders.translations)

    def existing_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ArtifactRef | None:
        local_ref = self._local_store.existing_object(
            stage=stage,
            ledger_tab=ledger_tab,
            version=version,
            candidate=candidate,
        )
        if local_ref is None:
            return None
        assert local_ref.path is not None
        drive_file = self._persist_drive_file(
            stage=stage,
            ledger_tab=ledger_tab,
            version=version,
            candidate=candidate,
            local_path=Path(local_ref.path),
            content_sha256=local_ref.sha256 or "",
            mime_type=local_ref.mime_type,
        )
        return ArtifactRef(
            kind=local_ref.kind,
            mime_type=local_ref.mime_type,
            url=drive_file.web_view_link,
            path=local_ref.path,
            sha256=local_ref.sha256,
            size_bytes=local_ref.size_bytes,
            source_ref=local_ref.source_ref,
            imsgx=local_ref.imsgx,
        )

    def persist_object(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
        object_: ProcessorObject,
    ) -> ArtifactRef:
        local_ref = self._local_store.persist_object(
            stage=stage,
            ledger_tab=ledger_tab,
            version=version,
            candidate=candidate,
            object_=object_,
        )
        assert local_ref.path is not None
        local_path = Path(local_ref.path)
        try:
            drive_file = self._persist_drive_file(
                stage=stage,
                ledger_tab=ledger_tab,
                version=version,
                candidate=candidate,
                local_path=local_path,
                content_sha256=local_ref.sha256 or "",
                mime_type=object_.mime_type,
            )
        except Exception:
            self._local_store.discard_object(local_ref)
            raise
        return ArtifactRef(
            kind=local_ref.kind,
            mime_type=local_ref.mime_type,
            url=drive_file.web_view_link,
            path=local_ref.path,
            sha256=local_ref.sha256,
            size_bytes=local_ref.size_bytes,
            source_ref=local_ref.source_ref,
            imsgx=local_ref.imsgx,
        )

    def discard_object(self, ref: ArtifactRef) -> None:
        if ref.url is not None and ref.url in self._created_drive_files_by_url:
            file_id = self._created_drive_files_by_url[ref.url]
            self.client.delete_file(file_id)
            del self._created_drive_files_by_url[ref.url]
        self._local_store.discard_object(ref)

    def _persist_drive_file(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
        local_path: Path,
        content_sha256: str,
        mime_type: str,
    ) -> DriveFile:
        folder_id = self._folder_id_for_ledger_tab(ledger_tab)
        name = local_path.name
        existing = self.client.find_file(folder_id=folder_id, name=name)
        if existing is not None:
            existing_sha256 = existing.app_properties.get(CURIO_SHA256_PROPERTY)
            if existing_sha256 != content_sha256:
                raise FileExistsError(
                    f"Google Drive artifact already exists with different or missing content hash: {name}"
                )
            return existing
        uploaded = self.client.upload_file(
            folder_id=folder_id,
            file_path=local_path,
            mime_type=mime_type,
            app_properties=_drive_app_properties(
                stage=stage,
                ledger_tab=ledger_tab,
                version=version,
                candidate=candidate,
                content_sha256=content_sha256,
            ),
        )
        self._created_drive_files_by_url[uploaded.web_view_link] = uploaded.id
        return uploaded

    def _folder_id_for_ledger_tab(self, ledger_tab: str) -> str:
        if ledger_tab == self.config.tabs.textifications:
            return self.config.drive_folders.textifications
        if ledger_tab == self.config.tabs.translations:
            return self.config.drive_folders.translations
        raise ValueError(f"unsupported Drive artifact ledger tab: {ledger_tab}")


class GoogleDriveClient:
    def __init__(self, session: GoogleSession) -> None:
        self.session = session

    def find_file(self, *, folder_id: str, name: str) -> DriveFile | None:
        response = self.session.get(
            f"{GOOGLE_DRIVE_API_BASE_URL}/files",
            params={
                "q": " and ".join(
                    (
                        "trashed = false",
                        f"'{_drive_query_literal(folder_id)}' in parents",
                        f"name = '{_drive_query_literal(name)}'",
                    )
                ),
                "pageSize": "2",
                "fields": f"files({GOOGLE_DRIVE_FILE_FIELDS})",
                "spaces": "drive",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            },
        )
        raise_for_status("search Google Drive", response)
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise RuntimeError("Google Drive API returned an invalid file search payload.")
        payload = cast(Mapping[str, object], payload)
        files = payload.get("files", [])
        if not isinstance(files, list):
            raise RuntimeError("Google Drive API returned an invalid file search payload.")
        if not files:
            return None
        if len(files) > 1:
            raise RuntimeError(f"Google Drive returned multiple artifacts named {name!r} in the configured folder.")
        return _drive_file_from_payload(files[0])

    def upload_file(
        self,
        *,
        folder_id: str,
        file_path: Path,
        mime_type: str,
        app_properties: Mapping[str, str],
    ) -> DriveFile:
        metadata = {
            "name": file_path.name,
            "parents": [folder_id],
            "appProperties": dict(app_properties),
        }
        boundary = f"===============curio-{uuid4().hex}"
        response = self.session.post(
            f"{GOOGLE_DRIVE_UPLOAD_API_BASE_URL}/files",
            params={"uploadType": "multipart", "fields": GOOGLE_DRIVE_FILE_FIELDS, "supportsAllDrives": "true"},
            data=_multipart_body(
                boundary=boundary,
                metadata=metadata,
                mime_type=mime_type,
                file_bytes=file_path.read_bytes(),
            ),
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
        )
        raise_for_status("upload Google Drive file", response)
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise RuntimeError("Google Drive API returned an invalid upload payload.")
        return _drive_file_from_payload(payload)

    def delete_file(self, file_id: str) -> None:
        response = self.session.delete(
            f"{GOOGLE_DRIVE_API_BASE_URL}/files/{file_id}",
            params={"supportsAllDrives": "true"},
        )
        raise_for_status("delete Google Drive file", response)

    def get_folder(self, folder_id: str) -> DriveFolder:
        response = self.session.get(
            f"{GOOGLE_DRIVE_API_BASE_URL}/files/{folder_id}",
            params={"fields": GOOGLE_DRIVE_FOLDER_FIELDS, "supportsAllDrives": "true"},
        )
        raise_for_status("read Google Drive folder", response)
        return _drive_folder_from_payload(response.json())


def _validate_local_artifact_directories(config: PipelineConfig) -> None:
    root = config.effective_artifact_root
    for path in (root, root / config.tabs.textifications, root / config.tabs.translations):
        _validate_writable_directory(path)


def _validate_writable_directory(path: Path) -> None:
    if path.exists() and not path.is_dir():
        raise NotADirectoryError(f"local artifact path is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    probe = path / f".curio-write-test-{uuid4().hex}"
    probe.write_bytes(b"")
    probe.unlink()


def _drive_folder_from_payload(payload: object) -> DriveFolder:
    if not isinstance(payload, Mapping):
        raise RuntimeError("Google Drive API returned an invalid folder payload.")

    data = cast(Mapping[str, object], payload)
    folder_id = data.get("id")
    name = data.get("name")
    mime_type = data.get("mimeType")
    trashed = data.get("trashed")
    if not isinstance(folder_id, str) or not folder_id:
        raise RuntimeError("Google Drive API returned a folder payload without an id.")
    if not isinstance(name, str) or not name:
        raise RuntimeError("Google Drive API returned a folder payload without a name.")
    if not isinstance(mime_type, str) or mime_type != GOOGLE_DRIVE_FOLDER_MIME_TYPE:
        raise RuntimeError(f"Configured Google Drive artifact target is not a folder: {name}")
    if not isinstance(trashed, bool):
        raise RuntimeError("Google Drive API returned a folder payload with invalid trashed status.")
    if trashed:
        raise RuntimeError(f"Configured Google Drive artifact folder is trashed: {name}")
    return DriveFolder(id=folder_id, name=name, mime_type=mime_type, trashed=trashed)


def _drive_file_from_payload(payload: object) -> DriveFile:
    if not isinstance(payload, Mapping):
        raise RuntimeError("Google Drive API returned an invalid file payload.")

    data = cast(Mapping[str, object], payload)
    file_id = data.get("id")
    name = data.get("name")
    mime_type = data.get("mimeType")
    web_view_link = data.get("webViewLink")
    parents = data.get("parents", [])
    app_properties = data.get("appProperties", {})
    size = data.get("size")
    if not isinstance(file_id, str) or not file_id:
        raise RuntimeError("Google Drive API returned a file payload without an id.")
    if not isinstance(name, str) or not name:
        raise RuntimeError("Google Drive API returned a file payload without a name.")
    if not isinstance(mime_type, str) or not mime_type:
        raise RuntimeError("Google Drive API returned a file payload without a mimeType.")
    if not isinstance(web_view_link, str) or not web_view_link:
        web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
    if not isinstance(parents, list):
        raise RuntimeError("Google Drive API returned a file payload with invalid parents.")
    if not isinstance(app_properties, Mapping):
        raise RuntimeError("Google Drive API returned a file payload with invalid appProperties.")

    return DriveFile(
        id=file_id,
        name=name,
        mime_type=mime_type,
        web_view_link=web_view_link,
        parents=tuple(parent for parent in parents if isinstance(parent, str)),
        app_properties={key: value for key, value in app_properties.items() if isinstance(key, str) and isinstance(value, str)},
        size_bytes=_optional_drive_size(size),
    )


def _drive_app_properties(
    *,
    stage: str,
    ledger_tab: str,
    version: str,
    candidate: ProcessCandidate,
    content_sha256: str,
) -> dict[str, str]:
    properties = {
        "curio_stage": stage,
        "curio_ledger_tab": ledger_tab,
        "curio_version": version,
        CURIO_SHA256_PROPERTY: content_sha256,
        "curio_source": candidate.source,
    }
    if candidate.source_ref.row_number is not None:
        properties["curio_source_row"] = str(candidate.source_ref.row_number)
    if candidate.imsgx.row_number is not None:
        properties["curio_imsgx_row"] = str(candidate.imsgx.row_number)
    return properties


def _multipart_body(
    *,
    boundary: str,
    metadata: Mapping[str, object],
    mime_type: str,
    file_bytes: bytes,
) -> bytes:
    metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    boundary_bytes = boundary.encode("ascii")
    return b"".join(
        (
            b"--",
            boundary_bytes,
            b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n",
            metadata_bytes,
            b"\r\n--",
            boundary_bytes,
            b"\r\nContent-Type: ",
            mime_type.encode("utf-8"),
            b"\r\n\r\n",
            file_bytes,
            b"\r\n--",
            boundary_bytes,
            b"--\r\n",
        )
    )


def _drive_query_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _optional_drive_size(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    raise RuntimeError("Google Drive API returned a file payload with invalid size.")
