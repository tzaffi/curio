import json
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import unquote

import pytest

import curio.pipeline.google_sheets as google_sheets_module
from curio.config import (
    GoogleConfig,
    KeychainLocator,
    PipelineConfig,
    PipelineTabsConfig,
)
from curio.google_api import GoogleApiError
from curio.pipeline import (
    ArtifactRef,
    GoogleSheetsClient,
    GoogleSheetsPipelineStore,
    GoogleSheetsPipelineStoreError,
    InMemoryArtifactStore,
    LedgerTab,
    PipelinePreviewAction,
    PipelineSelector,
    PipelineStage,
    ProcessorObject,
    ProcessRecord,
    ProcessRef,
    TextifyProcessor,
    TextifyProcessStatus,
    TranslateProcessStatus,
    run_processor_once,
)
from curio.pipeline.google_sheets import (
    DOWNLOAD_HEADERS,
    IMSGX_HEADERS,
    PROCESSOR_HEADERS,
)
from curio.textify import TextifyService


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


class FakeSession:
    def __init__(
        self,
        *,
        values_by_tab: Mapping[str, list[list[str]]],
        sheet_ids: Mapping[str, int] | None = None,
    ) -> None:
        self.values_by_tab = {tab: [list(row) for row in rows] for tab, rows in values_by_tab.items()}
        self.sheet_ids = dict(
            sheet_ids
            or {
                "iMsgX": 111,
                "downloads": 222,
                "textifications": 333,
                "translations": 444,
            }
        )
        self.calls: list[tuple[str, str, object]] = []

    def get(self, url: str, *, params: Mapping[str, str]) -> FakeResponse:
        self.calls.append(("GET", url, dict(params)))
        if url.endswith("/spreadsheet-id"):
            return FakeResponse(
                {
                    "sheets": [
                        {"properties": {"title": title, "sheetId": sheet_id}}
                        for title, sheet_id in self.sheet_ids.items()
                    ]
                }
            )
        tab = _tab_from_values_url(url)
        return FakeResponse({"values": self.values_by_tab[tab]})

    def post(self, url: str, *, params: Mapping[str, str], json: Mapping[str, object]) -> FakeResponse:
        self.calls.append(("POST", url, {"params": dict(params), "json": dict(json)}))
        tab = _tab_from_values_url(url.removesuffix(":append"))
        values = json["values"]
        assert isinstance(values, list)
        first_new_row = len(self.values_by_tab[tab]) + 1
        self.values_by_tab[tab].extend([list(row) for row in values])
        return FakeResponse({"updates": {"updatedRange": f"'{tab}'!A{first_new_row}:G{first_new_row}"}})

    def put(self, url: str, *, params: Mapping[str, str], json: Mapping[str, object]) -> FakeResponse:
        self.calls.append(("PUT", url, {"params": dict(params), "json": dict(json)}))
        tab = _tab_from_values_url(url)
        values = json["values"]
        assert isinstance(values, list)
        rows = self.values_by_tab.setdefault(tab, [])
        replacement = [list(row) for row in values]
        rows[: len(replacement)] = replacement
        return FakeResponse({})


class StaticSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response

    def get(self, url: str, *, params: Mapping[str, str]) -> FakeResponse:
        del url, params
        return self.response

    def post(self, url: str, *, params: Mapping[str, str], json: Mapping[str, object]) -> FakeResponse:
        del url, params, json
        return self.response

    def put(self, url: str, *, params: Mapping[str, str], json: Mapping[str, object]) -> FakeResponse:
        del url, params, json
        return self.response


def _tab_from_values_url(url: str) -> str:
    decoded = unquote(url.rsplit("/values/", maxsplit=1)[1])
    if decoded.startswith("'"):
        return decoded.split("'!", maxsplit=1)[0].strip("'")
    return decoded.split("!", maxsplit=1)[0]


def pipeline_config(downloads_dir: Path) -> PipelineConfig:
    return PipelineConfig(
        downloads_dir=downloads_dir,
        spreadsheet_id="spreadsheet-id",
        tabs=PipelineTabsConfig(
            imsgx="iMsgX",
            downloads="downloads",
            textifications="textifications",
            translations="translations",
        ),
    )


def imsgx_url(row_number: int = 8) -> str:
    return f"https://docs.google.com/spreadsheets/d/spreadsheet-id/edit#gid=111&range=A{row_number}:F{row_number}"


def downloads_url(row_number: int = 2) -> str:
    return f"https://docs.google.com/spreadsheets/d/spreadsheet-id/edit#gid=222&range=A{row_number}:G{row_number}"


def textification_url(row_number: int = 2) -> str:
    return f"https://docs.google.com/spreadsheets/d/spreadsheet-id/edit#gid=333&range=A{row_number}:G{row_number}"


def base_values(*, textifications: list[list[str]] | None = None, translations: list[list[str]] | None = None) -> dict[str, list[list[str]]]:
    return {
        "iMsgX": [
            list(IMSGX_HEADERS),
            ["2026-04-01 12:00:00 UTC", "2026-04-01 12:00:00 UTC", "message", "", "", "", "", "", ""],
        ],
        "downloads": [
            list(DOWNLOAD_HEADERS),
            [
                "2026-04-01 12:00:00 UTC",
                "2026-04-01 12:00:01 UTC",
                imsgx_url(),
                "https://x.com/example/status/203",
                "X1",
                "Image",
                "https://drive.google.com/file/d/object",
            ],
        ],
        "textifications": textifications if textifications is not None else [list(PROCESSOR_HEADERS)],
        "translations": translations if translations is not None else [list(PROCESSOR_HEADERS)],
    }


def make_store(tmp_path: Path, session: FakeSession, selector: PipelineSelector | None = None) -> GoogleSheetsPipelineStore:
    return GoogleSheetsPipelineStore(session=session, config=pipeline_config(tmp_path / "downloads"), selector=selector)


def test_google_sheets_store_builds_textify_candidate_from_downloads_row(tmp_path: Path) -> None:
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    local_artifact = downloads_dir / "imsgx-r0008-x1-image-203-photo-1.png"
    local_artifact.write_bytes(b"png")
    session = FakeSession(values_by_tab=base_values())

    candidate = make_store(tmp_path, session).next_candidate(PipelineStage.TEXTIFY.value)

    assert candidate is not None
    assert candidate.source == "https://x.com/example/status/203"
    assert candidate.source_ref.row_number == 2
    assert candidate.source_ref.row_url == downloads_url()
    assert candidate.source_ref.artifact_path == str(local_artifact)
    assert candidate.imsgx.row_number == 8
    assert candidate.imsgx.row_url == imsgx_url()
    assert candidate.artifact_key == local_artifact.name
    assert candidate.metadata["path"] == str(local_artifact)
    assert candidate.metadata["mime_type"] == "image/png"
    assert session.calls[0] == (
        "GET",
        "https://sheets.googleapis.com/v4/spreadsheets/spreadsheet-id",
        {"fields": "sheets(properties(sheetId,title))"},
    )


def test_google_sheets_store_exposes_textify_missing_artifact_diagnostics(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values())

    candidate = make_store(tmp_path, session).next_candidate(PipelineStage.TEXTIFY.value)

    assert candidate is not None
    assert candidate.metadata["downloads_dir"] == str(tmp_path / "downloads")
    assert candidate.metadata["expected_artifact_prefix"] == "imsgx-r0008-x1-image-"
    assert candidate.metadata["downloads_row"] == 2
    assert candidate.metadata["column"] == "X1"
    assert candidate.metadata["type"] == "Image"
    assert candidate.metadata["object"] == "https://drive.google.com/file/d/object"


def test_google_sheets_store_resolves_repo_zip_and_records_unsupported(tmp_path: Path) -> None:
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    repo_artifact = downloads_dir / "imsgx-r0100-x2-repo-xdevplatform-xmcp.zip"
    repo_artifact.write_bytes(b"zip")
    values = base_values()
    values["downloads"][1] = [
        "2026-04-06 23:53:05 UTC",
        "2026-04-05 23:39:23 UTC",
        imsgx_url(100),
        "https://github.com/xdevplatform/xmcp.git",
        "X2",
        "Repo",
        "https://drive.google.com/file/d/repo-object",
    ]
    session = FakeSession(values_by_tab=values)
    store = make_store(tmp_path, session)

    candidate = store.next_candidate(PipelineStage.TEXTIFY.value)

    assert candidate is not None
    assert candidate.metadata["path"] == str(repo_artifact)
    assert candidate.metadata["mime_type"] == "application/zip"
    assert candidate.metadata["expected_artifact_prefix"] == "imsgx-r0100-x2-repo-"

    result = run_processor_once(TextifyProcessor(TextifyService()), store=store, artifacts=InMemoryArtifactStore())

    assert result.record is not None
    assert result.record.status == TextifyProcessStatus.UNSUPPORTED.value
    assert result.record.object_ is None
    assert session.values_by_tab["textifications"][-1] == [
        "2026-04-06 23:53:05 UTC",
        "2026-04-05 23:39:23 UTC",
        imsgx_url(100),
        "Repo",
        downloads_url(),
        TextifyProcessStatus.UNSUPPORTED.value,
        "",
    ]


def test_google_sheets_store_skips_existing_textification_and_finds_existing_record(tmp_path: Path) -> None:
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.CONVERTED.value,
            "/tmp/textification.json",
        ],
    ]
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))
    candidate = store._textify_candidate(store._downloads[0])

    assert store.next_candidate(PipelineStage.TEXTIFY.value) is None
    record = store.existing_record(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
    )
    assert record is not None
    assert record.status == TextifyProcessStatus.CONVERTED.value
    assert record.object_ is not None
    assert record.object_.path == "/tmp/textification.json"


def test_google_sheets_store_appends_textification_rows_with_raw_insert(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values())
    store = make_store(tmp_path, session)
    candidate = store._textify_candidate(store._downloads[0])
    record = ProcessRecord(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        source_ref=candidate.source_ref,
        imsgx=candidate.imsgx,
        status=TextifyProcessStatus.CONVERTED.value,
        object_=ArtifactRef(kind="textify_object", mime_type="application/json", path="/tmp/textification.json"),
    )

    assert store.append_record(record) == record

    method, url, payload = session.calls[-1]
    assert method == "POST"
    assert url == "https://sheets.googleapis.com/v4/spreadsheets/spreadsheet-id/values/%27textifications%27%21A%3AG:append"
    assert payload == {
        "params": {"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
        "json": {
            "majorDimension": "ROWS",
            "values": [
                [
                    "2026-04-01 12:00:00 UTC",
                    "2026-04-01 12:00:01 UTC",
                    imsgx_url(),
                    "Image",
                    downloads_url(),
                    TextifyProcessStatus.CONVERTED.value,
                    "/tmp/textification.json",
                ]
            ],
        },
    }


def test_google_sheets_store_initializes_empty_processor_tab_before_append(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values(textifications=[]))
    store = make_store(tmp_path, session)
    candidate = store.next_candidate(PipelineStage.TEXTIFY.value)
    assert candidate is not None

    store.append_record(
        ProcessRecord(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab=LedgerTab.TEXTIFICATIONS.value,
            version="processor-v1",
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
            status=TextifyProcessStatus.NO_TEXT.value,
        )
    )

    assert session.calls[-2] == (
        "PUT",
        "https://sheets.googleapis.com/v4/spreadsheets/spreadsheet-id/values/%27textifications%27%21A1%3AG1",
        {
            "params": {"valueInputOption": "RAW"},
            "json": {"majorDimension": "ROWS", "values": [list(PROCESSOR_HEADERS)]},
        },
    )
    assert session.calls[-1][0] == "POST"
    assert session.values_by_tab["textifications"][0] == list(PROCESSOR_HEADERS)
    assert session.values_by_tab["textifications"][1] == [
        "2026-04-01 12:00:00 UTC",
        "2026-04-01 12:00:01 UTC",
        imsgx_url(),
        "Image",
        downloads_url(),
        TextifyProcessStatus.NO_TEXT.value,
        "",
    ]


def test_google_sheets_store_builds_translate_candidate_from_textification_object(tmp_path: Path) -> None:
    textification_object = tmp_path / "textifications" / "imsgx-r0008-textify-x1-image-203.json"
    textification_object.parent.mkdir()
    textification_object.write_text(
        json.dumps(
            {
                "object": {
                    "source": {
                        "suggested_files": [
                            {
                                "suggested_path": "ocr.md",
                                "output_format": "markdown",
                                "text": "Bonjour",
                            }
                        ],
                        "detected_languages": ["fr"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.CONVERTED.value,
            str(textification_object),
        ],
    ]
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))

    candidate = store.next_candidate(PipelineStage.TRANSLATE.value)

    assert candidate is not None
    assert candidate.source_ref.row_url == textification_url()
    assert candidate.metadata["blocks"] == [
        {
            "block_id": 1,
            "name": "ocr.md",
            "source_language_hint": "fr",
            "text": "Bonjour",
            "context": {"textification_object": str(textification_object)},
        }
    ]


def test_google_sheets_store_appends_translation_rows_from_textification_source(tmp_path: Path) -> None:
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.ALREADY_TEXT.value,
            "",
        ],
    ]
    session = FakeSession(values_by_tab=base_values(textifications=textifications))
    store = make_store(tmp_path, session)
    candidate = store.next_candidate(PipelineStage.TRANSLATE.value)
    assert candidate is not None
    assert candidate.metadata["text"] == "https://drive.google.com/file/d/object"

    record = ProcessRecord(
        stage=PipelineStage.TRANSLATE.value,
        ledger_tab=LedgerTab.TRANSLATIONS.value,
        version="processor-v1",
        source_ref=candidate.source_ref,
        imsgx=candidate.imsgx,
        status=TranslateProcessStatus.ALREADY_ENGLISH.value,
    )

    store.append_record(record)

    assert session.values_by_tab["translations"][-1] == [
        "2026-04-01 12:00:00 UTC",
        "2026-04-01 12:00:01 UTC",
        imsgx_url(),
        "Image",
        textification_url(),
        TranslateProcessStatus.ALREADY_ENGLISH.value,
        "",
    ]


def test_google_sheets_store_translate_candidate_reads_already_text_tweet_artifact(tmp_path: Path) -> None:
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    tweet_artifact = downloads_dir / "imsgx-r0008-text-tweet-bcherny-status-2017.json"
    tweet_artifact.write_text(json.dumps({"text": "Already English tweet.", "lang": "en"}), encoding="utf-8")
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Tweet",
            downloads_url(),
            TextifyProcessStatus.ALREADY_TEXT.value,
            "",
        ],
    ]
    values = base_values(textifications=textifications)
    values["downloads"][1][4] = "Text"
    values["downloads"][1][5] = "Tweet"
    values["downloads"][1][6] = ""
    store = make_store(tmp_path, FakeSession(values_by_tab=values))

    candidate = store.next_candidate(PipelineStage.TRANSLATE.value)

    assert candidate is not None
    assert candidate.artifact_key == tweet_artifact.name
    assert candidate.metadata["text"] == "Already English tweet."
    assert candidate.metadata["source_language_hint"] == "en"
    assert candidate.metadata["context"]["text_source"] == f"artifact:{tweet_artifact}:text"


def test_google_sheets_already_text_artifact_extraction_helpers(tmp_path: Path) -> None:
    article_path = tmp_path / "article.json"
    raw_path = tmp_path / "note.txt"
    empty_path = tmp_path / "empty.txt"
    html_path = tmp_path / "page.html"
    article_path.write_text(json.dumps({"article": {"plain_text": " Article body. "}}), encoding="utf-8")
    raw_path.write_text(" Raw text file. ", encoding="utf-8")
    empty_path.write_text(" ", encoding="utf-8")
    html_path.write_text(
        """
        <html>
          <head>
            <title>Useful Page</title>
            <meta name="description" content="Helpful summary.">
            <script>not useful</script>
          </head>
          <body><h1>Main Heading</h1><p>Readable body.</p></body>
        </html>
        """,
        encoding="utf-8",
    )

    assert google_sheets_module._text_from_artifact(article_path).text == "Article body."
    assert google_sheets_module._text_from_artifact(raw_path).text == "Raw text file."
    assert google_sheets_module._text_from_artifact(html_path) == google_sheets_module._ExtractedText(
        "Useful Page Helpful summary. Main Heading Readable body.",
        None,
        "html_text",
    )
    assert google_sheets_module._text_from_json_mapping(
        {
            "article": {
                "title": "I wasted 80 hours and $800 setting up OpenClaw - so you don't have to.",
                "preview_text": "I tried everything. AWS servers, remote setups, wrong API keys, wrong models.",
            },
            "lang": "zxx",
            "text": "https://t.co/zFf6OgdaHX",
        }
    ) == google_sheets_module._ExtractedText(
        "I wasted 80 hours and $800 setting up OpenClaw - so you don't have to.\n\n"
        "I tried everything. AWS servers, remote setups, wrong API keys, wrong models.",
        None,
        "article.title_preview_text",
    )
    assert google_sheets_module._text_from_json_mapping(
        {
            "lang": "zxx",
            "text": "https://t.co/f4BOUjXmF8",
            "parent": {"text": "GOOGLE QUIETLY LAUNCHED OFFLINE AI DICTATION APP", "lang": "en"},
        }
    ) == google_sheets_module._ExtractedText(
        "GOOGLE QUIETLY LAUNCHED OFFLINE AI DICTATION APP",
        "en",
        "parent.text",
    )
    assert google_sheets_module._text_from_json_mapping(
        {
            "lang": "zxx",
            "text": "https://t.co/f4BOUjXmF8",
            "card": {
                "binding_values": {
                    "title": {"string_value": "GitHub - google-ai-edge/gallery"},
                    "description": {"string_value": "A gallery that showcases on-device ML/GenAI use cases."},
                }
            },
        }
    ) == google_sheets_module._ExtractedText(
        "GitHub - google-ai-edge/gallery",
        None,
        "card.title",
    )
    assert google_sheets_module._text_from_json_mapping({"card": {}}) is None
    assert google_sheets_module._is_url_only_text(" ") is False
    assert google_sheets_module._text_from_json_mapping(
        {"article": {"title": "Already complete.", "preview_text": "Already complete. More text."}}
    ) == google_sheets_module._ExtractedText(
        "Already complete. More text.",
        None,
        "article.title_preview_text",
    )
    assert google_sheets_module._text_from_json_mapping({"article": {"preview_text": "Preview only."}}) == google_sheets_module._ExtractedText(
        "Preview only.",
        None,
        "article.title_preview_text",
    )
    assert google_sheets_module._text_from_json_mapping({"article": {"title": "Title only.", "lang": "en"}}) == google_sheets_module._ExtractedText(
        "Title only.",
        "en",
        "article.title_preview_text",
    )
    assert google_sheets_module._text_from_json_mapping({"plain_text": " Plain. ", "language": "fr"}) == google_sheets_module._ExtractedText(
        "Plain.",
        "fr",
        "plain_text",
    )
    assert google_sheets_module._text_from_json_mapping({"data": {"text": " Data text. ", "lang": "ja"}}) == google_sheets_module._ExtractedText(
        "Data text.",
        "ja",
        "data.text",
    )
    assert google_sheets_module._text_from_json_mapping({"content": " Content text. "}) == google_sheets_module._ExtractedText(
        "Content text.",
        None,
        "content",
    )
    assert google_sheets_module._text_from_json_mapping({}) is None
    with pytest.raises(GoogleSheetsPipelineStoreError, match="Already-text download artifact is empty"):
        google_sheets_module._text_from_artifact(empty_path)


def test_google_sheets_store_applies_upstream_selectors(tmp_path: Path) -> None:
    values = base_values()
    values["downloads"].append(
        [
            "2026-04-03 12:00:00 UTC",
            "2026-04-03 12:00:01 UTC",
            imsgx_url(9),
            "https://x.com/example/status/204",
            "X2",
            "Image",
            "https://drive.google.com/file/d/object-2",
        ]
    )
    store = make_store(
        tmp_path,
        FakeSession(values_by_tab=values),
        PipelineSelector(from_row=3, to_row=3, source="https://x.com/example/status/204", start="2026-04-03", end="2026-04-04"),
    )

    candidate = store.next_candidate(PipelineStage.TEXTIFY.value)

    assert candidate is not None
    assert candidate.source_ref.row_number == 3
    assert candidate.source == "https://x.com/example/status/204"


def test_google_sheets_store_resolves_refs_and_rejects_bad_inputs(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values())
    store = make_store(tmp_path, session)
    ref = ProcessRef(stage="download", tab="downloads", source="source", row_number=4)

    resolved = store.resolve_ref(ref)

    assert resolved.row_url == "https://docs.google.com/spreadsheets/d/spreadsheet-id/edit#gid=222&range=A4:G4"
    assert store.resolve_ref(ProcessRef(stage="unknown", tab="missing", source="source", row_number=4)).row_url is None
    with pytest.raises(GoogleSheetsPipelineStoreError, match="unsupported pipeline stage"):
        store.next_candidate("dossier")
    with pytest.raises(GoogleSheetsPipelineStoreError, match="unsupported append ledger tab"):
        store.append_record(
            ProcessRecord(
                stage=PipelineStage.TEXTIFY.value,
                ledger_tab="dossiers",
                version="processor-v1",
                source_ref=ref,
                imsgx=ref,
                status="converted",
            )
        )
    with pytest.raises(ValueError, match="row"):
        PipelineSelector(row=0)


def test_google_sheets_store_validates_tabs_and_headers(tmp_path: Path) -> None:
    with pytest.raises(GoogleSheetsPipelineStoreError, match="tab was not found"):
        make_store(tmp_path, FakeSession(values_by_tab=base_values(), sheet_ids={"iMsgX": 111}))

    values = base_values()
    values["downloads"] = [["bad"]]
    with pytest.raises(GoogleSheetsPipelineStoreError, match="header must exactly match"):
        make_store(tmp_path, FakeSession(values_by_tab=values))

    values = base_values()
    values["downloads"] = []
    with pytest.raises(GoogleSheetsPipelineStoreError, match="must have header"):
        make_store(tmp_path, FakeSession(values_by_tab=values))

    values = base_values()
    values["iMsgX"] = []
    with pytest.raises(GoogleSheetsPipelineStoreError, match="must have header"):
        make_store(tmp_path, FakeSession(values_by_tab=values))

    values = base_values()
    values["textifications"] = [["bad"]]
    with pytest.raises(GoogleSheetsPipelineStoreError, match="header must exactly match"):
        make_store(tmp_path, FakeSession(values_by_tab=values))


def test_google_sheets_client_rejects_invalid_payloads_and_http_errors() -> None:
    client = GoogleSheetsClient(StaticSession(FakeResponse([], status_code=500, reason="Error", text="boom")), "sheet")
    with pytest.raises(GoogleApiError, match="Unable to read Google Sheet"):
        client.read_values(sheet_name="tab", coordinates="A:G")

    client = GoogleSheetsClient(StaticSession(FakeResponse([], status_code=500, reason="Error")), "sheet")
    with pytest.raises(GoogleApiError, match="HTTP 500 Error"):
        client.read_values(sheet_name="tab", coordinates="A:G")

    client = GoogleSheetsClient(StaticSession(FakeResponse([])), "sheet")
    with pytest.raises(GoogleSheetsPipelineStoreError, match="invalid values payload"):
        client.read_values(sheet_name="tab", coordinates="A:G")

    client = GoogleSheetsClient(StaticSession(FakeResponse({"values": "bad"})), "sheet")
    with pytest.raises(GoogleSheetsPipelineStoreError, match="invalid values payload"):
        client.read_values(sheet_name="tab", coordinates="A:G")

    client = GoogleSheetsClient(StaticSession(FakeResponse([])), "sheet")
    assert client.append_values(sheet_name="tab", coordinates="A:G", values=[["value"]]) is None

    client = GoogleSheetsClient(StaticSession(FakeResponse({"updates": "bad"})), "sheet")
    assert client.append_values(sheet_name="tab", coordinates="A:G", values=[["value"]]) is None

    client = GoogleSheetsClient(StaticSession(FakeResponse({"updates": {"updatedRange": 7}})), "sheet")
    assert client.append_values(sheet_name="tab", coordinates="A:G", values=[["value"]]) is None

    client = GoogleSheetsClient(StaticSession(FakeResponse({"sheets": "bad"})), "sheet")
    with pytest.raises(GoogleSheetsPipelineStoreError, match="invalid spreadsheet metadata"):
        client.read_sheet_ids()

    client = GoogleSheetsClient(StaticSession(FakeResponse([])), "sheet")
    with pytest.raises(GoogleSheetsPipelineStoreError, match="invalid spreadsheet metadata"):
        client.read_sheet_ids()

    client = GoogleSheetsClient(
        StaticSession(
            FakeResponse(
                {
                    "sheets": [
                        [],
                        {"properties": []},
                        {"properties": {"title": 3, "sheetId": "bad"}},
                        {"properties": {"title": "ok", "sheetId": 1}},
                    ]
                }
            )
        ),
        "sheet",
    )
    assert client.read_sheet_ids() == {"ok": "1"}

    client = GoogleSheetsClient(StaticSession(FakeResponse({"updates": {}})), "sheet")
    assert client.append_values(sheet_name="tab", coordinates="A:G", values=[["value"]]) is None

    client = GoogleSheetsClient(StaticSession(FakeResponse([], status_code=500, reason="Error", text="boom")), "sheet")
    with pytest.raises(GoogleApiError, match="Unable to write Google Sheet header"):
        client.update_values(sheet_name="tab", coordinates="A1:G1", values=[["Date"]])


def test_google_sheets_store_rejects_unreadable_textification_objects(tmp_path: Path) -> None:
    textification_object = tmp_path / "bad.json"
    textification_object.write_text("[]", encoding="utf-8")
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.CONVERTED.value,
            str(textification_object),
        ],
    ]
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))

    with pytest.raises(GoogleSheetsPipelineStoreError, match="JSON object"):
        store.next_candidate(PipelineStage.TRANSLATE.value)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("not-json", "Unable to read textification object"),
        ({"object": []}, "payload must be a JSON object"),
        ({"object": {"source": []}}, "source must be a JSON object"),
        ({"object": {"source": {"suggested_files": []}}}, "no suggested text files"),
        ({"object": {"source": {"suggested_files": [[]]}}}, "suggested file must be an object"),
        ({"object": {"source": {"suggested_files": [{"text": ""}]}}}, "text must not be empty"),
    ],
)
def test_google_sheets_store_rejects_malformed_textification_objects(
    tmp_path: Path,
    payload: object,
    message: str,
) -> None:
    textification_object = tmp_path / "bad-textification.json"
    if isinstance(payload, str):
        textification_object.write_text(payload, encoding="utf-8")
    else:
        textification_object.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(GoogleSheetsPipelineStoreError, match=message):
        google_sheets_module._translation_blocks_from_textification_object(str(textification_object))


def test_google_sheets_store_uses_fallback_translation_block_for_unreadable_object_ref() -> None:
    assert google_sheets_module._translation_blocks_from_textification_object("https://drive/object") == [
        {
            "block_id": 1,
            "name": "textification_object",
            "source_language_hint": None,
            "text": "https://drive/object",
            "context": {"object": "https://drive/object"},
        }
    ]


def test_google_sheets_store_uses_default_block_names_when_missing_suggested_path(tmp_path: Path) -> None:
    textification_object = tmp_path / "textification.json"
    textification_object.write_text(
        json.dumps({"object": {"source": {"suggested_files": [{"text": "Bonjour"}]}}}),
        encoding="utf-8",
    )

    assert google_sheets_module._translation_blocks_from_textification_object(str(textification_object))[0]["name"] == "textification_1"


def test_google_sheets_store_normalizes_textification_detected_language_names(tmp_path: Path) -> None:
    textification_object = tmp_path / "textification.json"
    textification_object.write_text(
        json.dumps(
            {
                "object": {
                    "source": {
                        "detected_languages": ["English"],
                        "suggested_files": [{"suggested_path": "note.md", "text": "Already English."}],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    assert google_sheets_module._translation_blocks_from_textification_object(str(textification_object))[0] == {
        "block_id": 1,
        "name": "note.md",
        "source_language_hint": "en",
        "text": "Already English.",
        "context": {"textification_object": str(textification_object)},
    }


def test_google_sheets_store_defensive_branches_and_factory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    values = base_values()
    values["downloads"].insert(1, ["", "", "", "", "", "", ""])
    values["downloads"][2][2] = "not-a-row-url"
    local_object = tmp_path / "object.txt"
    local_object.write_text("text", encoding="utf-8")
    values["downloads"][2][6] = str(local_object)
    values["textifications"] = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            "different-imsgx",
            "Image",
            "different-source",
            "failed",
            "",
        ],
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            "different-imsgx",
            "Image",
            downloads_url(3),
            TextifyProcessStatus.CONVERTED.value,
            "",
        ],
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            "not-a-row-url",
            "Image",
            downloads_url(3),
            TextifyProcessStatus.UNSUPPORTED.value,
            "",
        ],
    ]
    session = FakeSession(values_by_tab=values)
    config = pipeline_config(tmp_path / "downloads")
    monkeypatch.setattr("curio.pipeline.google_sheets.build_authorized_session", lambda google_config, scopes: session)

    store = GoogleSheetsPipelineStore.from_config(
        google_config=GoogleConfig(
            oauth_client_credentials_path=tmp_path / "client.json",
            authorized_user_keychain=KeychainLocator(service="svc", account="acct"),
        ),
        pipeline_config=config,
    )
    candidate = store._textify_candidate(store._downloads[0])
    assert candidate.source_ref.artifact_path == str(local_object)
    assert candidate.imsgx.row_url is None
    existing = store.existing_record(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        candidate=candidate,
    )
    assert existing is not None
    assert existing.status == TextifyProcessStatus.UNSUPPORTED.value
    assert store.next_candidate(PipelineStage.TRANSLATE.value) is None
    assert store._textification_for_download(store._downloads[0]) is not None
    assert store.resolve_ref(ProcessRef(stage="download", tab="downloads", source="source", row_url="already")) == ProcessRef(
        stage="download",
        tab="downloads",
        source="source",
        row_url="already",
    )
    assert store.resolve_ref(ProcessRef(stage="download", tab="downloads", source="source")).row_url is None

    with pytest.raises(GoogleSheetsPipelineStoreError, match="unsupported processor tab"):
        store.existing_record(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab="bogus",
            version="processor-v1",
            candidate=candidate,
        )
    with pytest.raises(GoogleSheetsPipelineStoreError, match="unknown downloads source"):
        store.append_record(
            ProcessRecord(
                stage=PipelineStage.TEXTIFY.value,
                ledger_tab=LedgerTab.TEXTIFICATIONS.value,
                version="processor-v1",
                source_ref=ProcessRef(stage="download", tab="downloads", source="missing"),
                imsgx=candidate.imsgx,
                status=TextifyProcessStatus.CONVERTED.value,
            )
        )
    with pytest.raises(GoogleSheetsPipelineStoreError, match="unknown textification source"):
        store.append_record(
            ProcessRecord(
                stage=PipelineStage.TRANSLATE.value,
                ledger_tab=LedgerTab.TRANSLATIONS.value,
                version="processor-v1",
                source_ref=ProcessRef(stage="textify", tab="textifications", source="missing"),
                imsgx=candidate.imsgx,
                status=TranslateProcessStatus.TRANSLATED.value,
            )
        )
    with pytest.raises(GoogleSheetsPipelineStoreError, match="unsupported record stage"):
        store.append_record(
            ProcessRecord(
                stage="custom",
                ledger_tab=LedgerTab.TEXTIFICATIONS.value,
                version="processor-v1",
                source_ref=candidate.source_ref,
                imsgx=candidate.imsgx,
                status="converted",
            )
        )


def test_google_sheets_store_existing_record_miss_branches(tmp_path: Path) -> None:
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            "different-imsgx",
            "Image",
            downloads_url(),
            TextifyProcessStatus.CONVERTED.value,
            "",
        ],
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            "different-source",
            TextifyProcessStatus.CONVERTED.value,
            "",
        ],
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            "failed",
            "",
        ],
    ]
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))
    candidate = store._textify_candidate(store._downloads[0])

    assert (
        store.existing_record(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab=LedgerTab.TEXTIFICATIONS.value,
            version="processor-v1",
            candidate=candidate,
        )
        is None
    )


def test_google_sheets_store_translate_candidate_no_textification_paths(tmp_path: Path) -> None:
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(row=3))
    assert store.next_candidate(PipelineStage.TRANSLATE.value) is None

    store = make_store(tmp_path, FakeSession(values_by_tab=base_values()))
    assert store.next_candidate(PipelineStage.TRANSLATE.value) is None
    assert store._textification_for_download(store._downloads[0]) is None


def test_google_sheets_store_ignores_blank_processor_rows_and_missing_imsgx_url(tmp_path: Path) -> None:
    values = base_values(textifications=[list(PROCESSOR_HEADERS), ["", "", "", "", "", "", ""]])
    values["downloads"][1][2] = "not-a-row-url"
    store = make_store(tmp_path, FakeSession(values_by_tab=values))

    candidate = store.next_candidate(PipelineStage.TEXTIFY.value)

    assert candidate is not None
    assert candidate.imsgx.row_url is None
    assert candidate.source_ref.artifact_path is None


def test_google_sheets_store_translate_candidate_skips_existing_translation(tmp_path: Path) -> None:
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.ALREADY_TEXT.value,
            "",
        ],
    ]
    translations = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            textification_url(),
            TranslateProcessStatus.TRANSLATED.value,
            "https://drive/translation",
        ],
    ]
    store = make_store(
        tmp_path,
        FakeSession(values_by_tab=base_values(textifications=textifications, translations=translations)),
    )

    assert store.next_candidate(PipelineStage.TRANSLATE.value) is None


def test_google_sheets_store_selector_rejects_empty_strings_and_filters_each_bound(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source"):
        PipelineSelector(source=" ")
    with pytest.raises(ValueError, match="start"):
        PipelineSelector(start=" ")
    with pytest.raises(ValueError, match="end"):
        PipelineSelector(end=" ")

    assert make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(row=3)).next_candidate(PipelineStage.TEXTIFY.value) is None
    assert make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(from_row=3)).next_candidate(PipelineStage.TEXTIFY.value) is None
    assert make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(to_row=1)).next_candidate(PipelineStage.TEXTIFY.value) is None
    assert make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(source="missing")).next_candidate(PipelineStage.TEXTIFY.value) is None
    assert make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(start="2026-04-02")).next_candidate(PipelineStage.TEXTIFY.value) is None
    assert make_store(tmp_path, FakeSession(values_by_tab=base_values()), PipelineSelector(end="2026-03-31")).next_candidate(PipelineStage.TEXTIFY.value) is None


def test_google_sheets_store_previews_textify_without_mutation(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values())
    store = make_store(tmp_path, session)

    items = store.preview_stage(PipelineStage.TEXTIFY.value, limit=10)

    assert len(items) == 1
    item = items[0]
    assert item.stage == PipelineStage.TEXTIFY.value
    assert item.downloads_row == 2
    assert item.source == "https://x.com/example/status/203"
    assert item.input_ref is not None
    assert item.input_ref.row_number == 2
    assert item.action == PipelinePreviewAction.WOULD_PROCESS
    assert item.reason == "no textifications row records this downloads input"
    assert item.existing_record_ref is None
    assert all(call[0] == "GET" for call in session.calls)

    with pytest.raises(ValueError, match="limit"):
        store.preview_stage(PipelineStage.TEXTIFY.value, limit=0)
    with pytest.raises(GoogleSheetsPipelineStoreError, match="unsupported pipeline stage"):
        store.preview_stage("dossier", limit=1)


def test_google_sheets_store_previews_textify_with_empty_owned_tab_without_mutation(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values(textifications=[]))
    store = make_store(tmp_path, session)

    item = store.preview_stage(PipelineStage.TEXTIFY.value, limit=10)[0]

    assert item.action == PipelinePreviewAction.WOULD_PROCESS
    assert item.reason == "no textifications row records this downloads input"
    assert session.values_by_tab["textifications"] == []
    assert all(call[0] == "GET" for call in session.calls)


def test_google_sheets_store_preview_respects_limit_and_selector_filters(tmp_path: Path) -> None:
    values = base_values()
    values["downloads"].append(
        [
            "2026-04-03 12:00:00 UTC",
            "2026-04-03 12:00:01 UTC",
            imsgx_url(9),
            "https://x.com/example/status/204",
            "X2",
            "Text",
            "Bonjour.",
        ]
    )
    textify_limited = make_store(tmp_path, FakeSession(values_by_tab=values)).preview_stage(PipelineStage.TEXTIFY.value, limit=1)
    textify_filtered = make_store(
        tmp_path,
        FakeSession(values_by_tab=values),
        PipelineSelector(source="https://x.com/example/status/204"),
    ).preview_stage(PipelineStage.TEXTIFY.value, limit=10)
    translate_limited = make_store(tmp_path, FakeSession(values_by_tab=values)).preview_stage(PipelineStage.TRANSLATE.value, limit=1)
    translate_filtered = make_store(
        tmp_path,
        FakeSession(values_by_tab=values),
        PipelineSelector(source="https://x.com/example/status/204"),
    ).preview_stage(PipelineStage.TRANSLATE.value, limit=10)

    assert [item.downloads_row for item in textify_limited] == [2]
    assert [item.downloads_row for item in textify_filtered] == [3]
    assert [item.downloads_row for item in translate_limited] == [2]
    assert [item.downloads_row for item in translate_filtered] == [3]


def test_google_sheets_store_previews_existing_textify_record(tmp_path: Path) -> None:
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.CONVERTED.value,
            "/tmp/textification.json",
        ],
    ]
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))

    item = store.preview_stage(PipelineStage.TEXTIFY.value, limit=10)[0]

    assert item.action == PipelinePreviewAction.ALREADY_RECORDED
    assert item.existing_status == TextifyProcessStatus.CONVERTED.value
    assert item.existing_record_ref is not None
    assert item.existing_record_ref.tab == "textifications"
    assert item.existing_record_ref.row_number == 2
    assert item.reason == "textifications row 2 already has status converted"


def test_google_sheets_store_previews_translate_waiting_and_blocked_inputs(tmp_path: Path) -> None:
    waiting_store = make_store(tmp_path, FakeSession(values_by_tab=base_values()))

    waiting = waiting_store.preview_stage(PipelineStage.TRANSLATE.value, limit=10)[0]

    assert waiting.action == PipelinePreviewAction.WAITING_FOR_INPUT
    assert waiting.input_ref is None
    assert waiting.reason == "no textifications row exists for this downloads input"

    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Image",
            downloads_url(),
            TextifyProcessStatus.UNSUPPORTED.value,
            "",
        ],
    ]
    blocked_store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))

    blocked = blocked_store.preview_stage(PipelineStage.TRANSLATE.value, limit=10)[0]

    assert blocked.action == PipelinePreviewAction.BLOCKED
    assert blocked.input_ref is not None
    assert blocked.input_ref.tab == "textifications"
    assert blocked.existing_status == TextifyProcessStatus.UNSUPPORTED.value
    assert blocked.reason == "textifications row 2 status unsupported is not translatable"


def test_google_sheets_store_previews_translate_process_and_existing_record(tmp_path: Path) -> None:
    textifications = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Text",
            downloads_url(),
            TextifyProcessStatus.ALREADY_TEXT.value,
            "",
        ],
    ]
    store = make_store(tmp_path, FakeSession(values_by_tab=base_values(textifications=textifications)))

    item = store.preview_stage(PipelineStage.TRANSLATE.value, limit=10)[0]

    assert item.action == PipelinePreviewAction.WOULD_PROCESS
    assert item.input_ref is not None
    assert item.input_ref.tab == "textifications"
    assert item.reason == "eligible textifications row 2 has no translation row"

    empty_translations_session = FakeSession(values_by_tab=base_values(textifications=textifications, translations=[]))
    empty_translations_store = make_store(tmp_path, empty_translations_session)
    empty_translations_item = empty_translations_store.preview_stage(PipelineStage.TRANSLATE.value, limit=10)[0]

    assert empty_translations_item.action == PipelinePreviewAction.WOULD_PROCESS
    assert empty_translations_session.values_by_tab["translations"] == []
    assert all(call[0] == "GET" for call in empty_translations_session.calls)

    translations = [
        list(PROCESSOR_HEADERS),
        [
            "2026-04-01 12:00:00 UTC",
            "2026-04-01 12:00:01 UTC",
            imsgx_url(),
            "Text",
            textification_url(),
            TranslateProcessStatus.ALREADY_ENGLISH.value,
            "",
        ],
    ]
    existing_store = make_store(
        tmp_path,
        FakeSession(values_by_tab=base_values(textifications=textifications, translations=translations)),
    )

    existing = existing_store.preview_stage(PipelineStage.TRANSLATE.value, limit=10)[0]

    assert existing.action == PipelinePreviewAction.ALREADY_RECORDED
    assert existing.existing_status == TranslateProcessStatus.ALREADY_ENGLISH.value
    assert existing.existing_record_ref is not None
    assert existing.existing_record_ref.tab == "translations"
    assert existing.existing_record_ref.row_number == 2
    assert existing.reason == "translations row 2 already has status already_english"


def test_google_sheets_helper_fallbacks(tmp_path: Path) -> None:
    config = pipeline_config(tmp_path / "downloads")

    assert google_sheets_module._input_stage_for_record_stage("custom") == "custom"
    assert google_sheets_module._input_tab_for_record_stage("custom", config) == "custom"
    assert google_sheets_module._input_stage_for_record_stage(PipelineStage.TRANSLATE.value) == PipelineStage.TEXTIFY.value
    assert google_sheets_module._input_tab_for_record_stage(PipelineStage.TRANSLATE.value, config) == "textifications"
    assert google_sheets_module._last_column_for_tab("iMsgX", config) == "I"


def test_google_sheets_store_uses_fallback_row_number_when_append_response_omits_range(tmp_path: Path) -> None:
    class NoRangeSession(FakeSession):
        def post(self, url: str, *, params: Mapping[str, str], json: Mapping[str, object]) -> FakeResponse:
            self.calls.append(("POST", url, {"params": dict(params), "json": dict(json)}))
            tab = _tab_from_values_url(url.removesuffix(":append"))
            values = json["values"]
            assert isinstance(values, list)
            self.values_by_tab[tab].extend([list(row) for row in values])
            return FakeResponse({})

    session = NoRangeSession(values_by_tab=base_values())
    store = make_store(tmp_path, session)
    candidate = store.next_candidate(PipelineStage.TEXTIFY.value)
    assert candidate is not None
    store.append_record(
        ProcessRecord(
            stage=PipelineStage.TEXTIFY.value,
            ledger_tab=LedgerTab.TEXTIFICATIONS.value,
            version="processor-v1",
            source_ref=candidate.source_ref,
            imsgx=candidate.imsgx,
            status=TextifyProcessStatus.NO_TEXT.value,
        )
    )

    assert store._textifications[-1].row_number == 2


def test_google_sheets_store_can_persist_objects_through_real_processor_shape(tmp_path: Path) -> None:
    session = FakeSession(values_by_tab=base_values())
    store = make_store(tmp_path, session)
    candidate = store.next_candidate(PipelineStage.TEXTIFY.value)
    assert candidate is not None
    object_ = ProcessorObject(payload={"ok": True})

    record = ProcessRecord(
        stage=PipelineStage.TEXTIFY.value,
        ledger_tab=LedgerTab.TEXTIFICATIONS.value,
        version="processor-v1",
        source_ref=candidate.source_ref,
        imsgx=candidate.imsgx,
        status=TextifyProcessStatus.CONVERTED.value,
        object_=ArtifactRef(kind="textify_object", mime_type=object_.mime_type, url="https://drive/object"),
    )

    store.append_record(record)

    assert session.values_by_tab["textifications"][-1][-1] == "https://drive/object"
