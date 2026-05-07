from collections.abc import Mapping
from pathlib import Path

import pytest

import curio.pipeline.drive as drive_module
from curio.config import (
    PipelineConfig,
    PipelineDriveFoldersConfig,
    PipelineTabsConfig,
)
from curio.google_api import GOOGLE_PIPELINE_SCOPES, GoogleApiError
from curio.pipeline import (
    GoogleDriveArtifactStore,
    GoogleDriveClient,
    PipelineStage,
    ProcessCandidate,
    ProcessorObject,
    ProcessRef,
)
from curio.pipeline.local import LocalArtifactStore


class FakeResponse:
    def __init__(
        self,
        payload: object,
        *,
        status_code: int = 200,
        reason: str = "OK",
        text: str = "",
    ) -> None:
        self.payload = payload
        self.status_code = status_code
        self.reason = reason
        self.text = text

    def json(self) -> object:
        return self.payload


class FakeDriveSession:
    def __init__(
        self,
        *,
        search_files: list[dict[str, object]] | None = None,
        folders: Mapping[str, dict[str, object]] | None = None,
    ) -> None:
        self.search_files = [] if search_files is None else list(search_files)
        self.folders = {
            "folder-textifications": folder_payload("folder-textifications", "textifications"),
            "folder-translations": folder_payload("folder-translations", "translations"),
            **({} if folders is None else dict(folders)),
        }
        self.calls: list[tuple[str, str, dict[str, object]]] = []
        self.next_upload_id = "drive-file-1"

    def get(self, url: str, *, params: Mapping[str, str]) -> FakeResponse:
        self.calls.append(("GET", url, {"params": dict(params)}))
        folder_prefix = "https://www.googleapis.com/drive/v3/files/"
        if url.startswith(folder_prefix) and url != "https://www.googleapis.com/drive/v3/files":
            folder_id = url.removeprefix(folder_prefix)
            return FakeResponse(self.folders[folder_id])
        return FakeResponse({"files": list(self.search_files)})

    def post(
        self,
        url: str,
        *,
        params: Mapping[str, str],
        json: Mapping[str, object] | None = None,
        data: bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> FakeResponse:
        del json
        self.calls.append(
            (
                "POST",
                url,
                {
                    "params": dict(params),
                    "data": b"" if data is None else data,
                    "headers": {} if headers is None else dict(headers),
                },
            )
        )
        return FakeResponse(
            {
                "id": self.next_upload_id,
                "name": "uploaded.json",
                "mimeType": "application/json",
                "webViewLink": f"https://drive.google.com/file/d/{self.next_upload_id}/view",
                "parents": ["folder-textifications"],
                "appProperties": {},
                "size": "123",
            }
        )

    def put(self, url: str, *, params: Mapping[str, str], json: Mapping[str, object]) -> FakeResponse:
        del url, params, json
        return FakeResponse({})

    def delete(self, url: str, *, params: Mapping[str, str]) -> FakeResponse:
        self.calls.append(("DELETE", url, {"params": dict(params)}))
        return FakeResponse({})


def pipeline_config(tmp_path: Path) -> PipelineConfig:
    return PipelineConfig(
        downloads_dir=tmp_path / "downloads",
        artifact_root=tmp_path / "artifacts",
        spreadsheet_id="spreadsheet-id",
        tabs=PipelineTabsConfig(
            imsgx="iMsgX",
            downloads="downloads",
            textifications="textifications",
            translations="translations",
        ),
        drive_folders=PipelineDriveFoldersConfig(
            textifications="folder-textifications",
            translations="folder-translations",
        ),
    )


def make_candidate() -> ProcessCandidate:
    ref = ProcessRef(
        stage="download",
        tab="downloads",
        source="https://x.com/example/status/203",
        row_number=8,
        artifact_path="/Users/zeph/Desktop/iMsgX/downloads/imsgx-r0008-x1-image-203-photo-1.png",
    )
    return ProcessCandidate(
        source_ref=ref,
        imsgx=ref,
        source=ref.source,
        artifact_key=Path(ref.artifact_path or "").name,
        metadata={"type": "Image"},
    )


def drive_file_payload(*, sha256: str, file_id: str = "existing-file") -> dict[str, object]:
    return {
        "id": file_id,
        "name": "artifact.json",
        "mimeType": "application/json",
        "webViewLink": f"https://drive.google.com/file/d/{file_id}/view",
        "parents": ["folder-textifications"],
        "appProperties": {"curio_sha256": sha256},
        "size": "123",
    }


def folder_payload(
    folder_id: str,
    name: str,
    *,
    trashed: bool = False,
    mime_type: str = drive_module.GOOGLE_DRIVE_FOLDER_MIME_TYPE,
) -> dict[str, object]:
    return {
        "id": folder_id,
        "name": name,
        "mimeType": mime_type,
        "trashed": trashed,
    }


def make_store(tmp_path: Path, session: FakeDriveSession) -> GoogleDriveArtifactStore:
    return GoogleDriveArtifactStore(
        root=tmp_path / "artifacts",
        config=pipeline_config(tmp_path),
        client=GoogleDriveClient(session),
    )


def test_google_drive_artifact_store_from_config_requests_pipeline_scopes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}

    def fake_build_authorized_session(google_config: object, *, scopes: list[str]) -> FakeDriveSession:
        captured["google_config"] = google_config
        captured["scopes"] = scopes
        return FakeDriveSession()

    monkeypatch.setattr("curio.pipeline.drive.build_authorized_session", fake_build_authorized_session)

    store = GoogleDriveArtifactStore.from_config(
        google_config="google-config",  # type: ignore[arg-type]
        pipeline_config=pipeline_config(tmp_path),
    )

    assert isinstance(store, GoogleDriveArtifactStore)
    assert captured == {"google_config": "google-config", "scopes": GOOGLE_PIPELINE_SCOPES}


def test_google_drive_artifact_store_uploads_local_json_to_processor_folder(tmp_path: Path) -> None:
    session = FakeDriveSession()
    store = make_store(tmp_path, session)

    ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab="textifications",
        version="processor-v1",
        candidate=make_candidate(),
        object_=ProcessorObject(payload={"text": "hello"}),
    )

    assert ref.path is not None
    assert Path(ref.path).exists()
    assert Path(ref.path).name == "imsgx-r0008-textify-x1-image-203-photo-1.json"
    assert ref.url == "https://drive.google.com/file/d/drive-file-1/view"
    get_call = session.calls[0]
    assert get_call[0] == "GET"
    assert "'folder-textifications' in parents" in str(get_call[2]["params"]["q"])
    post_call = session.calls[1]
    assert post_call[0] == "POST"
    assert post_call[1] == "https://www.googleapis.com/upload/drive/v3/files"
    assert b'"parents":["folder-textifications"]' in post_call[2]["data"]
    assert b'"curio_stage":"textify"' in post_call[2]["data"]
    assert b'"curio_sha256":"' in post_call[2]["data"]
    assert str(post_call[2]["headers"]["Content-Type"]).startswith("multipart/related; boundary=")


def test_google_drive_artifact_store_existing_object_returns_none_without_local_file(tmp_path: Path) -> None:
    session = FakeDriveSession()
    store = make_store(tmp_path, session)

    assert (
        store.existing_object(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab="textifications",
            version="processor-v1",
            candidate=make_candidate(),
        )
        is None
    )
    assert session.calls == []


def test_google_drive_artifact_store_existing_object_uploads_existing_local_file(tmp_path: Path) -> None:
    candidate = make_candidate()
    LocalArtifactStore(tmp_path / "artifacts").persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab="textifications",
        version="processor-v1",
        candidate=candidate,
        object_=ProcessorObject(payload={"text": "existing"}),
    )
    session = FakeDriveSession()
    store = make_store(tmp_path, session)

    ref = store.existing_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab="textifications",
        version="processor-v1",
        candidate=candidate,
    )

    assert ref is not None
    assert ref.path is not None
    assert Path(ref.path).exists()
    assert ref.url == "https://drive.google.com/file/d/drive-file-1/view"
    assert [call[0] for call in session.calls] == ["GET", "POST"]
    assert b'"curio_sha256":"' in session.calls[1][2]["data"]


def test_google_drive_artifact_store_uploads_translations_to_translation_folder(tmp_path: Path) -> None:
    session = FakeDriveSession()
    store = make_store(tmp_path, session)

    ref = store.persist_object(
        stage=PipelineStage.TRANSLATE.value,
        ledger_tab="translations",
        version="processor-v1",
        candidate=make_candidate(),
        object_=ProcessorObject(payload={"translation": "hello"}),
    )

    assert ref.path is not None
    assert Path(ref.path).parent == tmp_path / "artifacts" / "translations"
    assert "'folder-translations' in parents" in str(session.calls[0][2]["params"]["q"])
    assert b'"parents":["folder-translations"]' in session.calls[1][2]["data"]


def test_google_drive_artifact_store_reuses_existing_same_content_file(tmp_path: Path) -> None:
    first_session = FakeDriveSession()
    first_ref = make_store(tmp_path, first_session).persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab="textifications",
        version="processor-v1",
        candidate=make_candidate(),
        object_=ProcessorObject(payload={"text": "hello"}),
    )
    assert first_ref.sha256 is not None
    reuse_session = FakeDriveSession(search_files=[drive_file_payload(sha256=first_ref.sha256)])

    reused_ref = make_store(tmp_path, reuse_session).persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab="textifications",
        version="processor-v1",
        candidate=make_candidate(),
        object_=ProcessorObject(payload={"text": "hello"}),
    )

    assert reused_ref.url == "https://drive.google.com/file/d/existing-file/view"
    assert [call[0] for call in reuse_session.calls] == ["GET"]


def test_google_drive_artifact_store_rejects_same_name_different_content_and_discards_local_file(
    tmp_path: Path,
) -> None:
    session = FakeDriveSession(search_files=[drive_file_payload(sha256="different")])
    store = make_store(tmp_path, session)

    with pytest.raises(FileExistsError, match="different or missing content hash"):
        store.persist_object(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab="textifications",
            version="processor-v1",
            candidate=make_candidate(),
            object_=ProcessorObject(payload={"text": "hello"}),
        )

    artifact_dir = tmp_path / "artifacts" / "textifications"
    assert not any(artifact_dir.glob("*.json"))
    assert [call[0] for call in session.calls] == ["GET"]


def test_google_drive_artifact_store_discards_created_local_and_drive_files(tmp_path: Path) -> None:
    session = FakeDriveSession()
    store = make_store(tmp_path, session)
    ref = store.persist_object(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab="textifications",
        version="processor-v1",
        candidate=make_candidate(),
        object_=ProcessorObject(payload={"text": "hello"}),
    )
    assert ref.path is not None

    store.discard_object(ref)

    assert not Path(ref.path).exists()
    assert session.calls[-1] == (
        "DELETE",
        "https://www.googleapis.com/drive/v3/files/drive-file-1",
        {"params": {"supportsAllDrives": "true"}},
    )


def test_google_drive_artifact_store_from_config_validates_local_and_drive_targets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    session = FakeDriveSession()

    monkeypatch.setattr(
        "curio.pipeline.drive.build_authorized_session",
        lambda _google_config, *, scopes: session,
    )

    GoogleDriveArtifactStore.from_config(
        google_config="google-config",  # type: ignore[arg-type]
        pipeline_config=pipeline_config(tmp_path),
    )

    assert (tmp_path / "artifacts" / "textifications").is_dir()
    assert (tmp_path / "artifacts" / "translations").is_dir()
    assert [call[1] for call in session.calls] == [
        "https://www.googleapis.com/drive/v3/files/folder-textifications",
        "https://www.googleapis.com/drive/v3/files/folder-translations",
    ]


def test_google_drive_artifact_store_from_config_rejects_file_artifact_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "artifact-root"
    artifact_root.write_text("not a directory", encoding="utf-8")
    config = PipelineConfig(
        downloads_dir=tmp_path / "downloads",
        artifact_root=artifact_root,
        spreadsheet_id="spreadsheet-id",
        tabs=PipelineTabsConfig(
            imsgx="iMsgX",
            downloads="downloads",
            textifications="textifications",
            translations="translations",
        ),
        drive_folders=PipelineDriveFoldersConfig(
            textifications="folder-textifications",
            translations="folder-translations",
        ),
    )

    monkeypatch.setattr(
        "curio.pipeline.drive.build_authorized_session",
        lambda _google_config, *, scopes: FakeDriveSession(),
    )

    with pytest.raises(NotADirectoryError, match="local artifact path is not a directory"):
        GoogleDriveArtifactStore.from_config(
            google_config="google-config",  # type: ignore[arg-type]
            pipeline_config=config,
        )


def test_google_drive_artifact_store_rejects_unknown_ledger_tab(tmp_path: Path) -> None:
    store = make_store(tmp_path, FakeDriveSession())

    with pytest.raises(ValueError, match="unsupported Drive artifact ledger tab"):
        store._folder_id_for_ledger_tab("dossiers")


def test_google_drive_client_rejects_bad_payloads_and_http_errors(tmp_path: Path) -> None:
    class StaticSession(FakeDriveSession):
        def __init__(self, response: FakeResponse) -> None:
            super().__init__()
            self.response = response

        def get(self, url: str, *, params: Mapping[str, str]) -> FakeResponse:
            del url, params
            return self.response

        def post(
            self,
            url: str,
            *,
            params: Mapping[str, str],
            json: Mapping[str, object] | None = None,
            data: bytes | None = None,
            headers: Mapping[str, str] | None = None,
        ) -> FakeResponse:
            del url, params, json, data, headers
            return self.response

    client = GoogleDriveClient(StaticSession(FakeResponse([], status_code=500, reason="Error", text="boom")))
    with pytest.raises(GoogleApiError, match="Unable to search Google Drive"):
        client.find_file(folder_id="folder", name="name.json")

    client = GoogleDriveClient(StaticSession(FakeResponse([])))
    with pytest.raises(RuntimeError, match="invalid file search payload"):
        client.find_file(folder_id="folder", name="name.json")

    client = GoogleDriveClient(StaticSession(FakeResponse({"files": "bad"})))
    with pytest.raises(RuntimeError, match="invalid file search payload"):
        client.find_file(folder_id="folder", name="name.json")

    client = GoogleDriveClient(StaticSession(FakeResponse({"files": [{}, {}]})))
    with pytest.raises(RuntimeError, match="multiple artifacts"):
        client.find_file(folder_id="folder", name="name.json")

    upload_path = tmp_path / "payload.json"
    upload_path.write_text("{}", encoding="utf-8")
    client = GoogleDriveClient(StaticSession(FakeResponse([])))
    with pytest.raises(RuntimeError, match="invalid upload payload"):
        client.upload_file(
            folder_id="folder",
            file_path=upload_path,
            mime_type="application/json",
            app_properties={},
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "invalid file payload"),
        ({"name": "artifact.json", "mimeType": "application/json"}, "without an id"),
        ({"id": "file-id", "mimeType": "application/json"}, "without a name"),
        ({"id": "file-id", "name": "artifact.json"}, "without a mimeType"),
        (
            {"id": "file-id", "name": "artifact.json", "mimeType": "application/json", "parents": "folder"},
            "invalid parents",
        ),
        (
            {"id": "file-id", "name": "artifact.json", "mimeType": "application/json", "appProperties": []},
            "invalid appProperties",
        ),
        (
            {"id": "file-id", "name": "artifact.json", "mimeType": "application/json", "size": "large"},
            "invalid size",
        ),
    ],
)
def test_google_drive_file_payload_validation(payload: object, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        drive_module._drive_file_from_payload(payload)


def test_google_drive_file_payload_defaults_and_optional_size_branches() -> None:
    without_size = drive_module._drive_file_from_payload(
        {
            "id": "file-id",
            "name": "artifact.json",
            "mimeType": "application/json",
            "parents": ["folder", 7],
            "appProperties": {"curio_sha256": "sha", 3: "ignored", "bad": 5},
        }
    )
    with_int_size = drive_module._drive_file_from_payload(
        {
            "id": "file-id",
            "name": "artifact.json",
            "mimeType": "application/json",
            "parents": ["folder"],
            "appProperties": {},
            "size": 456,
        }
    )

    assert without_size.web_view_link == "https://drive.google.com/file/d/file-id/view"
    assert without_size.parents == ("folder",)
    assert without_size.app_properties == {"curio_sha256": "sha"}
    assert without_size.size_bytes is None
    assert with_int_size.size_bytes == 456


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "invalid folder payload"),
        (
            {"name": "textifications", "mimeType": drive_module.GOOGLE_DRIVE_FOLDER_MIME_TYPE, "trashed": False},
            "without an id",
        ),
        (
            {"id": "folder-id", "mimeType": drive_module.GOOGLE_DRIVE_FOLDER_MIME_TYPE, "trashed": False},
            "without a name",
        ),
        (folder_payload("file-id", "file", mime_type="application/json"), "not a folder"),
        (
            {"id": "folder-id", "name": "textifications", "mimeType": drive_module.GOOGLE_DRIVE_FOLDER_MIME_TYPE},
            "invalid trashed status",
        ),
        (folder_payload("folder-id", "textifications", trashed=True), "folder is trashed"),
    ],
)
def test_google_drive_folder_payload_validation(payload: object, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        drive_module._drive_folder_from_payload(payload)
