import json
import mimetypes
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from html.parser import HTMLParser
from pathlib import Path
from typing import Final, Self, cast
from urllib.parse import quote

from curio.config import GoogleConfig, PipelineConfig
from curio.google_api import (
    GOOGLE_PIPELINE_SCOPES,
    GoogleSession,
    build_authorized_session,
    raise_for_status,
)
from curio.pipeline.models import (
    ArtifactRef,
    JsonObject,
    JsonValue,
    PipelinePreviewAction,
    PipelinePreviewItem,
    PipelineStage,
    ProcessCandidate,
    ProcessRecord,
    ProcessRef,
    TextifyProcessStatus,
)
from curio.translate import normalize_language_hint

GOOGLE_SHEETS_API_BASE_URL: Final = "https://sheets.googleapis.com/v4/spreadsheets"
IMSGX_HEADERS: Final = (
    "Date",
    "X Date",
    "Text",
    "X1",
    "X2",
    "X3",
    "X1 Source ID",
    "X2 Source ID",
    "X3 Source ID",
)
DOWNLOAD_HEADERS: Final = ("Date", "X Date", "iMsgX", "Source", "Column", "Type", "Object")
PROCESSOR_HEADERS: Final = ("Date", "X Date", "iMsgX", "Type", "Source", "Status", "Object", "Local")
PROCESSOR_REQUIRED_HEADERS: Final = ("Date", "X Date", "iMsgX", "Type", "Source", "Status", "Object")
_ROW_URL_RE: Final = re.compile(r"docs\.google\.com/spreadsheets/d/([^/]+)/edit#gid=(\d+)&range=[A-Z]+(\d+)")
_UPDATED_RANGE_ROW_RE: Final = re.compile(r"![A-Z]+(\d+):")
_SLUG_RE: Final = re.compile(r"[^a-z0-9]+")
_URL_ONLY_RE: Final = re.compile(r"(?:https?://|www\.|t\.co/|pic\.x\.com/)\S+", re.IGNORECASE)


class GoogleSheetsPipelineStoreError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PipelineSelector:
    row: int | None = None
    from_row: int | None = None
    to_row: int | None = None
    source: str | None = None
    start: str | None = None
    end: str | None = None

    def __post_init__(self) -> None:
        for name, value in (("row", self.row), ("from_row", self.from_row), ("to_row", self.to_row)):
            if value is not None and value < 1:
                raise ValueError(f"{name} must be a positive row number")
        if self.source is not None and not self.source.strip():
            raise ValueError("source must not be empty")
        if self.start is not None and not self.start.strip():
            raise ValueError("start must not be empty")
        if self.end is not None and not self.end.strip():
            raise ValueError("end must not be empty")


@dataclass(frozen=True, slots=True)
class _DownloadRow:
    row_number: int
    date: str
    x_date: str
    imsgx: str
    source: str
    column: str
    type_: str
    object_value: str


@dataclass(frozen=True, slots=True)
class _ProcessorRow:
    row_number: int
    date: str
    x_date: str
    imsgx: str
    type_: str
    source: str
    status: str
    object_value: str
    local_value: str


@dataclass(frozen=True, slots=True)
class _StagedProcessorRow:
    values: tuple[str, ...]
    processor_row: _ProcessorRow


@dataclass(frozen=True, slots=True)
class _ExtractedText:
    text: str
    source_language_hint: str | None
    source: str


class GoogleSheetsClient:
    def __init__(self, session: GoogleSession, spreadsheet_id: str) -> None:
        self.session = session
        self.spreadsheet_id = spreadsheet_id

    def read_values(self, *, sheet_name: str, coordinates: str) -> list[list[str]]:
        encoded_range = quote(_sheet_range(sheet_name, coordinates), safe="")
        response = self.session.get(
            f"{GOOGLE_SHEETS_API_BASE_URL}/{self.spreadsheet_id}/values/{encoded_range}",
            params={"majorDimension": "ROWS"},
        )
        raise_for_status("read Google Sheet", response)
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise GoogleSheetsPipelineStoreError("Google Sheets API returned an invalid values payload.")
        payload = cast(Mapping[str, object], payload)
        values = payload.get("values", [])
        if not isinstance(values, list):
            raise GoogleSheetsPipelineStoreError("Google Sheets API returned an invalid values payload.")
        return [[str(cell) for cell in row] for row in values if isinstance(row, list)]

    def append_values(self, *, sheet_name: str, coordinates: str, values: Sequence[Sequence[str]]) -> int | None:
        encoded_range = quote(_sheet_range(sheet_name, coordinates), safe="")
        response = self.session.post(
            f"{GOOGLE_SHEETS_API_BASE_URL}/{self.spreadsheet_id}/values/{encoded_range}:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"majorDimension": "ROWS", "values": [list(row) for row in values]},
        )
        raise_for_status("append Google Sheet rows", response)
        payload = response.json()
        if not isinstance(payload, Mapping):
            return None
        payload = cast(Mapping[str, object], payload)
        updates = payload.get("updates")
        if not isinstance(updates, Mapping):
            return None
        updates = cast(Mapping[str, object], updates)
        updated_range = updates.get("updatedRange")
        if not isinstance(updated_range, str):
            return None
        return _parse_updated_range_row(updated_range)

    def update_values(self, *, sheet_name: str, coordinates: str, values: Sequence[Sequence[str]]) -> None:
        encoded_range = quote(_sheet_range(sheet_name, coordinates), safe="")
        response = self.session.put(
            f"{GOOGLE_SHEETS_API_BASE_URL}/{self.spreadsheet_id}/values/{encoded_range}",
            params={"valueInputOption": "RAW"},
            json={"majorDimension": "ROWS", "values": [list(row) for row in values]},
        )
        raise_for_status("write Google Sheet header", response)

    def read_sheet_ids(self) -> Mapping[str, str]:
        response = self.session.get(
            f"{GOOGLE_SHEETS_API_BASE_URL}/{self.spreadsheet_id}",
            params={"fields": "sheets(properties(sheetId,title))"},
        )
        raise_for_status("read Google Sheet metadata", response)
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise GoogleSheetsPipelineStoreError("Google Sheets API returned an invalid spreadsheet metadata payload.")
        payload = cast(Mapping[str, object], payload)
        sheets = payload.get("sheets")
        if not isinstance(sheets, list):
            raise GoogleSheetsPipelineStoreError("Google Sheets API returned an invalid spreadsheet metadata payload.")
        sheet_ids: dict[str, str] = {}
        for candidate in sheets:
            if not isinstance(candidate, Mapping):
                continue
            candidate = cast(Mapping[str, object], candidate)
            properties = candidate.get("properties")
            if not isinstance(properties, Mapping):
                continue
            properties = cast(Mapping[str, object], properties)
            title = properties.get("title")
            sheet_id = properties.get("sheetId")
            if isinstance(title, str) and isinstance(sheet_id, int):
                sheet_ids[title] = str(sheet_id)
        return sheet_ids


class GoogleSheetsPipelineStore:
    def __init__(
        self,
        *,
        session: GoogleSession,
        config: PipelineConfig,
        selector: PipelineSelector | None = None,
    ) -> None:
        self.config = config
        self.selector = selector or PipelineSelector()
        self.client = GoogleSheetsClient(session, config.spreadsheet_id)
        self._sheet_ids = dict(self.client.read_sheet_ids())
        self._require_sheet_ids()
        self._empty_processor_tabs: set[str] = set()
        self._processor_headers: dict[str, tuple[str, ...]] = {}
        self._staged_processor_rows: dict[str, list[_StagedProcessorRow]] = {}
        self._validate_imsgx_header()
        self._downloads = self._read_download_rows()
        self._textifications = self._read_processor_rows(config.tabs.textifications)
        self._translations = self._read_processor_rows(config.tabs.translations)

    @classmethod
    def from_config(
        cls,
        *,
        google_config: GoogleConfig,
        pipeline_config: PipelineConfig,
        selector: PipelineSelector | None = None,
    ) -> Self:
        session = build_authorized_session(google_config, scopes=GOOGLE_PIPELINE_SCOPES)
        return cls(session=session, config=pipeline_config, selector=selector)

    def next_candidate(self, stage: str) -> ProcessCandidate | None:
        if stage == PipelineStage.TEXTIFY.value:
            return self._next_textify_candidate()
        if stage == PipelineStage.TRANSLATE.value:
            return self._next_translate_candidate()
        raise GoogleSheetsPipelineStoreError(f"unsupported pipeline stage for current scope: {stage}")

    def unprocessed_candidate_count(self, stage: str) -> int:
        if stage == PipelineStage.TEXTIFY.value:
            return sum(1 for _candidate in self._iter_textify_candidates())
        if stage == PipelineStage.TRANSLATE.value:
            return sum(1 for _candidate in self._iter_translate_candidates())
        raise GoogleSheetsPipelineStoreError(f"unsupported pipeline stage for current scope: {stage}")

    def preview_stage(self, stage: str, *, limit: int) -> tuple[PipelinePreviewItem, ...]:
        if limit < 1:
            raise ValueError("limit must be a positive integer")
        if stage == PipelineStage.TEXTIFY.value:
            return tuple(self._preview_textify(limit=limit))
        if stage == PipelineStage.TRANSLATE.value:
            return tuple(self._preview_translate(limit=limit))
        raise GoogleSheetsPipelineStoreError(f"unsupported pipeline stage for current scope: {stage}")

    def existing_record(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        candidate: ProcessCandidate,
    ) -> ProcessRecord | None:
        rows = self._processor_rows_for_tab(ledger_tab)
        for row in reversed(rows):
            if not _visible_source_matches_ref(row.source, candidate.source_ref):
                continue
            if not _visible_source_matches_ref(row.imsgx, candidate.imsgx):
                continue
            return self._process_record_from_row(stage=stage, ledger_tab=ledger_tab, version=version, row=row)
        return None

    def stage_record(self, record: ProcessRecord) -> ProcessRecord:
        if record.ledger_tab not in {self.config.tabs.textifications, self.config.tabs.translations}:
            raise GoogleSheetsPipelineStoreError(f"unsupported stage ledger tab: {record.ledger_tab}")

        self._ensure_processor_header(record.ledger_tab)
        row = self._record_values(record)
        headers = self._processor_headers_for_tab(record.ledger_tab)
        processor_row = _ProcessorRow(
            row_number=self._next_local_processor_row_number(record.ledger_tab),
            date=_row_cell(row, headers, "Date"),
            x_date=_row_cell(row, headers, "X Date"),
            imsgx=_row_cell(row, headers, "iMsgX"),
            type_=_row_cell(row, headers, "Type"),
            source=_row_cell(row, headers, "Source"),
            status=_row_cell(row, headers, "Status"),
            object_value=_row_cell(row, headers, "Object"),
            local_value=_processor_local_value(row, headers),
        )
        self._processor_rows_for_tab(record.ledger_tab).append(processor_row)
        self._staged_processor_rows.setdefault(record.ledger_tab, []).append(
            _StagedProcessorRow(values=tuple(row), processor_row=processor_row)
        )
        return record

    def flush_records(self) -> None:
        for tab, staged_rows in list(self._staged_processor_rows.items()):
            headers = self._processor_headers_for_tab(tab)
            appended_row_number = self.client.append_values(
                sheet_name=tab,
                coordinates=f"A:{_column_name(len(headers))}",
                values=[staged.values for staged in staged_rows],
            )
            if appended_row_number is not None:
                self._renumber_staged_processor_rows(tab, staged_rows, first_row_number=appended_row_number)
            del self._staged_processor_rows[tab]

    def discard_staged_records(self) -> None:
        for tab, staged_rows in self._staged_processor_rows.items():
            rows = self._processor_rows_for_tab(tab)
            for staged in reversed(staged_rows):
                rows.remove(staged.processor_row)
        self._staged_processor_rows.clear()

    def resolve_ref(self, ref: ProcessRef) -> ProcessRef:
        if ref.row_url is not None or ref.row_number is None:
            return ref
        sheet_id = self._sheet_ids.get(ref.tab)
        if sheet_id is None:
            return ref
        return ProcessRef(
            stage=ref.stage,
            tab=ref.tab,
            source=ref.source,
            row_number=ref.row_number,
            row_url=_row_url(
                spreadsheet_id=self.config.spreadsheet_id,
                sheet_id=sheet_id,
                row_number=ref.row_number,
                last_column=self._last_column_for_tab(ref.tab),
            ),
            spreadsheet_id=ref.spreadsheet_id,
            sheet_id=ref.sheet_id,
            artifact_url=ref.artifact_url,
            artifact_path=ref.artifact_path,
            artifact_sha256=ref.artifact_sha256,
        )

    def _next_textify_candidate(self) -> ProcessCandidate | None:
        return next(self._iter_textify_candidates(), None)

    def _iter_textify_candidates(self) -> Iterator[ProcessCandidate]:
        for row in self._downloads:
            if not self._selector_matches(row):
                continue
            candidate = self._textify_candidate(row)
            if self._has_any_processor_row(self._textifications, candidate):
                continue
            yield candidate

    def _next_translate_candidate(self) -> ProcessCandidate | None:
        return next(self._iter_translate_candidates(), None)

    def _iter_translate_candidates(self) -> Iterator[ProcessCandidate]:
        for download in self._downloads:
            if not self._selector_matches(download):
                continue
            textification = self._textification_for_download(download)
            if textification is None:
                continue
            if textification.status not in {
                TextifyProcessStatus.CONVERTED.value,
                TextifyProcessStatus.ALREADY_TEXT.value,
            }:
                continue
            candidate = self._translate_candidate(download, textification)
            if self._has_any_processor_row(self._translations, candidate):
                continue
            yield candidate

    def _preview_textify(self, *, limit: int) -> list[PipelinePreviewItem]:
        items: list[PipelinePreviewItem] = []
        for row in self._downloads:
            if len(items) >= limit:
                break
            if not self._selector_matches(row):
                continue
            candidate = self._textify_candidate(row)
            existing = self._matching_processor_row(self._textifications, candidate)
            if existing is None:
                items.append(
                    PipelinePreviewItem(
                        stage=PipelineStage.TEXTIFY.value,
                        downloads_row=row.row_number,
                        source=row.source,
                        input_ref=candidate.source_ref,
                        action=PipelinePreviewAction.WOULD_PROCESS,
                        reason=f"no {self.config.tabs.textifications} row records this downloads input",
                    )
                )
                continue
            items.append(
                PipelinePreviewItem(
                    stage=PipelineStage.TEXTIFY.value,
                    downloads_row=row.row_number,
                    source=row.source,
                    input_ref=candidate.source_ref,
                    action=PipelinePreviewAction.ALREADY_RECORDED,
                    reason=f"{self.config.tabs.textifications} row {existing.row_number} already has status {existing.status}",
                    existing_record_ref=self._processor_ref(
                        stage=PipelineStage.TEXTIFY.value,
                        tab=self.config.tabs.textifications,
                        row=existing,
                    ),
                    existing_status=existing.status,
                )
            )
        return items

    def _preview_translate(self, *, limit: int) -> list[PipelinePreviewItem]:
        items: list[PipelinePreviewItem] = []
        for download in self._downloads:
            if len(items) >= limit:
                break
            if not self._selector_matches(download):
                continue
            textification = self._textification_for_download(download)
            if textification is None:
                items.append(
                    PipelinePreviewItem(
                        stage=PipelineStage.TRANSLATE.value,
                        downloads_row=download.row_number,
                        source=download.source,
                        input_ref=None,
                        action=PipelinePreviewAction.WAITING_FOR_INPUT,
                        reason=f"no {self.config.tabs.textifications} row exists for this downloads input",
                    )
                )
                continue
            textification_ref = self._processor_ref(
                stage=PipelineStage.TEXTIFY.value,
                tab=self.config.tabs.textifications,
                row=textification,
            )
            if textification.status not in {
                TextifyProcessStatus.CONVERTED.value,
                TextifyProcessStatus.ALREADY_TEXT.value,
            }:
                items.append(
                    PipelinePreviewItem(
                        stage=PipelineStage.TRANSLATE.value,
                        downloads_row=download.row_number,
                        source=download.source,
                        input_ref=textification_ref,
                        action=PipelinePreviewAction.BLOCKED,
                        reason=(
                            f"{self.config.tabs.textifications} row {textification.row_number} "
                            f"status {textification.status} is not translatable"
                        ),
                        existing_record_ref=textification_ref,
                        existing_status=textification.status,
                    )
                )
                continue
            candidate = self._translate_candidate(download, textification)
            existing = self._matching_processor_row(self._translations, candidate)
            if existing is None:
                items.append(
                    PipelinePreviewItem(
                        stage=PipelineStage.TRANSLATE.value,
                        downloads_row=download.row_number,
                        source=download.source,
                        input_ref=candidate.source_ref,
                        action=PipelinePreviewAction.WOULD_PROCESS,
                        reason=f"eligible {self.config.tabs.textifications} row {textification.row_number} has no translation row",
                    )
                )
                continue
            items.append(
                PipelinePreviewItem(
                    stage=PipelineStage.TRANSLATE.value,
                    downloads_row=download.row_number,
                    source=download.source,
                    input_ref=candidate.source_ref,
                    action=PipelinePreviewAction.ALREADY_RECORDED,
                    reason=f"{self.config.tabs.translations} row {existing.row_number} already has status {existing.status}",
                    existing_record_ref=self._processor_ref(
                        stage=PipelineStage.TRANSLATE.value,
                        tab=self.config.tabs.translations,
                        row=existing,
                    ),
                    existing_status=existing.status,
                )
            )
        return items

    def _textify_candidate(self, row: _DownloadRow) -> ProcessCandidate:
        local_path = self._local_download_path(row)
        source_ref = self._download_ref(row, local_path=local_path)
        metadata = _download_metadata(row)
        metadata["downloads_dir"] = str(self.config.downloads_dir)
        expected_prefix = self._local_download_prefix(row)
        if expected_prefix is not None:
            metadata["expected_artifact_prefix"] = expected_prefix
        if local_path is not None:
            metadata.update(
                {
                    "path": str(local_path),
                    "name": local_path.name,
                    "mime_type": mimetypes.guess_type(local_path.name)[0],
                }
            )
        return ProcessCandidate(
            source_ref=source_ref,
            imsgx=self._imsgx_ref(row),
            source=row.source,
            artifact_key=None if local_path is None else local_path.name,
            metadata=metadata,
        )

    def _translate_candidate(self, download: _DownloadRow, textification: _ProcessorRow) -> ProcessCandidate:
        source_ref = self._processor_ref(
            stage=PipelineStage.TEXTIFY.value,
            tab=self.config.tabs.textifications,
            row=textification,
        )
        context = _download_metadata(download)
        metadata: JsonObject = {
            "date": download.date,
            "x_date": download.x_date,
            "imsgx": download.imsgx,
            "type": download.type_,
            "source": download.source,
            "downloads_row": download.row_number,
            "textification_row": textification.row_number,
            "context": context,
        }
        artifact_key = textification.local_value or textification.object_value or None
        if textification.status == TextifyProcessStatus.CONVERTED.value:
            object_ref = textification.local_value or textification.object_value
            metadata["blocks"] = _translation_blocks_from_textification_object(object_ref)
            artifact_key = object_ref or artifact_key
        else:
            local_path = self._local_download_path(download)
            extracted = _already_text_download_text(download, local_path=local_path)
            artifact_key = local_path.name if local_path is not None else artifact_key
            metadata["text"] = extracted.text
            metadata["name"] = _slugify(download.type_ or download.column)
            metadata["source_language_hint"] = extracted.source_language_hint
            metadata["context"] = {**context, "text_source": extracted.source}
        return ProcessCandidate(
            source_ref=source_ref,
            imsgx=self._imsgx_ref(download),
            source=download.source,
            artifact_key=artifact_key,
            metadata=metadata,
        )

    def _download_ref(self, row: _DownloadRow, *, local_path: Path | None) -> ProcessRef:
        artifact_url = row.object_value if _is_url(row.object_value) else None
        artifact_path = str(local_path) if local_path is not None else row.object_value if Path(row.object_value).is_absolute() else None
        return ProcessRef(
            stage="download",
            tab=self.config.tabs.downloads,
            source=row.source,
            row_number=row.row_number,
            row_url=self._row_url(self.config.tabs.downloads, row.row_number),
            spreadsheet_id=self.config.spreadsheet_id,
            sheet_id=self._sheet_ids[self.config.tabs.downloads],
            artifact_url=artifact_url,
            artifact_path=artifact_path,
        )

    def _imsgx_ref(self, row: _DownloadRow) -> ProcessRef:
        parsed = _parse_google_row_url(row.imsgx)
        row_number = parsed["row_number"] if parsed is not None else None
        sheet_id = parsed["sheet_id"] if parsed is not None else self._sheet_ids[self.config.tabs.imsgx]
        return ProcessRef(
            stage="imsgx",
            tab=self.config.tabs.imsgx,
            source=row.imsgx or row.source,
            row_number=row_number,
            row_url=row.imsgx if _is_url(row.imsgx) else None,
            spreadsheet_id=self.config.spreadsheet_id,
            sheet_id=sheet_id,
        )

    def _processor_ref(self, *, stage: str, tab: str, row: _ProcessorRow) -> ProcessRef:
        return ProcessRef(
            stage=stage,
            tab=tab,
            source=row.source,
            row_number=row.row_number,
            row_url=self._row_url(tab, row.row_number),
            spreadsheet_id=self.config.spreadsheet_id,
            sheet_id=self._sheet_ids[tab],
            artifact_url=row.object_value if _is_url(row.object_value) else None,
            artifact_path=_processor_artifact_path(row),
        )

    def _process_record_from_row(
        self,
        *,
        stage: str,
        ledger_tab: str,
        version: str,
        row: _ProcessorRow,
    ) -> ProcessRecord:
        return ProcessRecord(
            stage=stage,
            ledger_tab=ledger_tab,
            version=version,
            source_ref=_source_ref_from_visible_source(
                stage=_input_stage_for_record_stage(stage),
                tab=_input_tab_for_record_stage(stage, self.config),
                source=row.source,
                spreadsheet_id=self.config.spreadsheet_id,
            ),
            imsgx=_source_ref_from_visible_source(
                stage="imsgx",
                tab=self.config.tabs.imsgx,
                source=row.imsgx,
                spreadsheet_id=self.config.spreadsheet_id,
            ),
            status=row.status,
            object_=_artifact_ref_from_processor_row(stage=stage, row=row),
            metadata={
                "date": row.date,
                "x_date": row.x_date,
                "type": row.type_,
                "row_number": row.row_number,
            },
        )

    def _record_values(self, record: ProcessRecord) -> list[str]:
        if record.stage == PipelineStage.TEXTIFY.value:
            source_row = self._download_for_ref(record.source_ref)
            if source_row is None:
                raise GoogleSheetsPipelineStoreError("cannot stage textification row for unknown downloads source")
            date = source_row.date
            x_date = source_row.x_date
            imsgx = source_row.imsgx
            type_ = source_row.type_
        elif record.stage == PipelineStage.TRANSLATE.value:
            source_row = self._processor_row_for_ref(self._textifications, record.source_ref)
            if source_row is None:
                raise GoogleSheetsPipelineStoreError("cannot stage translation row for unknown textification source")
            date = source_row.date
            x_date = source_row.x_date
            imsgx = source_row.imsgx
            type_ = source_row.type_
        else:
            raise GoogleSheetsPipelineStoreError(f"unsupported record stage: {record.stage}")

        headers = self._processor_headers_for_tab(record.ledger_tab)
        values = {
            "Date": date,
            "X Date": x_date,
            "iMsgX": imsgx,
            "Type": type_,
            "Source": record.source_ref.row_url or record.source_ref.source,
            "Status": record.status,
            "Object": _artifact_url_cell(record.object_),
            "Local": _artifact_path_cell(record.object_),
        }
        if "Local" not in headers:
            values["Object"] = _legacy_artifact_ref_cell(record.object_)
        return [values.get(header, "") for header in headers]

    def _validate_imsgx_header(self) -> None:
        values = self.client.read_values(sheet_name=self.config.tabs.imsgx, coordinates="A:I")
        _validate_header(values, IMSGX_HEADERS, tab_name=self.config.tabs.imsgx)

    def _read_download_rows(self) -> list[_DownloadRow]:
        values = self.client.read_values(sheet_name=self.config.tabs.downloads, coordinates="A:G")
        _validate_header(values, DOWNLOAD_HEADERS, tab_name=self.config.tabs.downloads)
        rows: list[_DownloadRow] = []
        for row_number, raw_row in enumerate(values[1:], start=2):
            row = _normalize_row(raw_row, width=len(DOWNLOAD_HEADERS))
            if not any(value.strip() for value in row):
                continue
            rows.append(
                _DownloadRow(
                    row_number=row_number,
                    date=row[0],
                    x_date=row[1],
                    imsgx=row[2],
                    source=row[3],
                    column=row[4],
                    type_=row[5],
                    object_value=row[6],
                )
            )
        return rows

    def _read_processor_rows(self, tab_name: str) -> list[_ProcessorRow]:
        values = self.client.read_values(sheet_name=tab_name, coordinates="A:Z")
        if not values:
            self._empty_processor_tabs.add(tab_name)
            self._processor_headers[tab_name] = PROCESSOR_HEADERS
            return []
        header = _validate_processor_header(values, tab_name=tab_name)
        self._processor_headers[tab_name] = header
        rows: list[_ProcessorRow] = []
        for row_number, raw_row in enumerate(values[1:], start=2):
            row = _normalize_row(raw_row, width=len(header))
            if not any(value.strip() for value in row):
                continue
            rows.append(
                _ProcessorRow(
                    row_number=row_number,
                    date=_row_cell(row, header, "Date"),
                    x_date=_row_cell(row, header, "X Date"),
                    imsgx=_row_cell(row, header, "iMsgX"),
                    type_=_row_cell(row, header, "Type"),
                    source=_row_cell(row, header, "Source"),
                    status=_row_cell(row, header, "Status"),
                    object_value=_row_cell(row, header, "Object"),
                    local_value=_processor_local_value(row, header),
                )
            )
        return rows

    def _ensure_processor_header(self, tab_name: str) -> None:
        if tab_name not in self._empty_processor_tabs:
            return
        self.client.update_values(
            sheet_name=tab_name,
            coordinates=f"A1:{_column_name(len(PROCESSOR_HEADERS))}1",
            values=[self._processor_headers_for_tab(tab_name)],
        )
        self._empty_processor_tabs.remove(tab_name)

    def _processor_rows_for_tab(self, tab: str) -> list[_ProcessorRow]:
        if tab == self.config.tabs.textifications:
            return self._textifications
        if tab == self.config.tabs.translations:
            return self._translations
        raise GoogleSheetsPipelineStoreError(f"unsupported processor tab: {tab}")

    def _require_sheet_ids(self) -> None:
        required_tabs = (
            self.config.tabs.imsgx,
            self.config.tabs.downloads,
            self.config.tabs.textifications,
            self.config.tabs.translations,
        )
        for tab_name in required_tabs:
            if tab_name not in self._sheet_ids:
                raise GoogleSheetsPipelineStoreError(f"Configured Google Sheet tab was not found: {tab_name}")

    def _selector_matches(self, row: _DownloadRow) -> bool:
        selector = self.selector
        if selector.row is not None and row.row_number != selector.row:
            return False
        if selector.from_row is not None and row.row_number < selector.from_row:
            return False
        if selector.to_row is not None and row.row_number > selector.to_row:
            return False
        if selector.source is not None and selector.source not in {row.source, row.object_value, row.imsgx}:
            return False
        candidate_date = row.x_date or row.date
        if selector.start is not None and candidate_date < selector.start:
            return False
        if selector.end is not None and candidate_date > selector.end:
            return False
        return True

    def _has_any_processor_row(self, rows: Sequence[_ProcessorRow], candidate: ProcessCandidate) -> bool:
        return self._matching_processor_row(rows, candidate) is not None

    def _matching_processor_row(self, rows: Sequence[_ProcessorRow], candidate: ProcessCandidate) -> _ProcessorRow | None:
        for row in rows:
            if _visible_source_matches_ref(row.source, candidate.source_ref) and _visible_source_matches_ref(row.imsgx, candidate.imsgx):
                return row
        return None

    def _textification_for_download(self, download: _DownloadRow) -> _ProcessorRow | None:
        source_ref = self._download_ref(download, local_path=self._local_download_path(download))
        imsgx = self._imsgx_ref(download)
        for row in self._textifications:
            if _visible_source_matches_ref(row.source, source_ref) and _visible_source_matches_ref(row.imsgx, imsgx):
                return row
        return None

    def _download_for_ref(self, ref: ProcessRef) -> _DownloadRow | None:
        if ref.row_number is not None:
            for row in self._downloads:
                if row.row_number == ref.row_number:
                    return row
            return None
        if ref.row_url is not None:
            for row in self._downloads:
                if _visible_source_matches_ref(self._row_url(self.config.tabs.downloads, row.row_number), ref):
                    return row
            return None
        for row in self._downloads:
            if _visible_source_matches_ref(row.source, ref) or _visible_source_matches_ref(self._row_url(self.config.tabs.downloads, row.row_number), ref):
                return row
        return None

    def _processor_row_for_ref(self, rows: Sequence[_ProcessorRow], ref: ProcessRef) -> _ProcessorRow | None:
        if ref.row_number is not None:
            for row in rows:
                if row.row_number == ref.row_number:
                    return row
            return None
        if ref.row_url is not None:
            for row in rows:
                if _visible_source_matches_ref(self._row_url(ref.tab, row.row_number), ref):
                    return row
            return None
        for row in rows:
            if _visible_source_matches_ref(row.source, ref) or _visible_source_matches_ref(self._row_url(ref.tab, row.row_number), ref):
                return row
        return None

    def _local_download_path(self, row: _DownloadRow) -> Path | None:
        if row.object_value:
            object_path = Path(row.object_value).expanduser()
            if object_path.is_absolute() and object_path.exists():
                return object_path
        prefix = self._local_download_prefix(row)
        if prefix is None:
            return None
        matches = sorted(path for path in self.config.downloads_dir.glob(f"{prefix}*") if path.is_file())
        return matches[0] if matches else None

    def _local_download_prefix(self, row: _DownloadRow) -> str | None:
        imsgx_row = _parse_google_row_url(row.imsgx)
        if imsgx_row is None:
            return None
        return f"imsgx-r{imsgx_row['row_number']:04d}-{_slugify(row.column)}-{_slugify(row.type_)}-"

    def _row_url(self, tab: str, row_number: int) -> str:
        return _row_url(
            spreadsheet_id=self.config.spreadsheet_id,
            sheet_id=self._sheet_ids[tab],
            row_number=row_number,
            last_column=self._last_column_for_tab(tab),
        )

    def _last_column_for_tab(self, tab: str) -> str:
        if tab in {self.config.tabs.textifications, self.config.tabs.translations}:
            return _column_name(len(self._processor_headers_for_tab(tab)))
        return _last_column_for_tab(tab, self.config)

    def _processor_headers_for_tab(self, tab: str) -> tuple[str, ...]:
        return self._processor_headers.get(tab, PROCESSOR_HEADERS)

    def _next_local_processor_row_number(self, tab: str) -> int:
        return len(self._processor_rows_for_tab(tab)) + 2

    def _renumber_staged_processor_rows(
        self,
        tab: str,
        staged_rows: Sequence[_StagedProcessorRow],
        *,
        first_row_number: int,
    ) -> None:
        rows = self._processor_rows_for_tab(tab)
        for offset, staged in enumerate(staged_rows):
            index = rows.index(staged.processor_row)
            updated_row = replace(staged.processor_row, row_number=first_row_number + offset)
            rows[index] = updated_row


def _validate_header(values: Sequence[Sequence[str]], expected: Sequence[str], *, tab_name: str) -> None:
    if not values:
        raise GoogleSheetsPipelineStoreError(
            f"Configured Google Sheet tab '{tab_name}' must have header: " + ", ".join(expected)
        )
    header = tuple(values[0])
    if header != tuple(expected):
        raise GoogleSheetsPipelineStoreError(
            f"Configured Google Sheet tab '{tab_name}' header must exactly match: " + ", ".join(expected)
        )


def _validate_processor_header(values: Sequence[Sequence[str]], *, tab_name: str) -> tuple[str, ...]:
    if not values:
        raise GoogleSheetsPipelineStoreError(
            f"Configured Google Sheet tab '{tab_name}' must have header: " + ", ".join(PROCESSOR_HEADERS)
        )
    header = tuple(str(value) for value in values[0])
    missing = [column for column in PROCESSOR_REQUIRED_HEADERS if column not in header]
    if missing:
        raise GoogleSheetsPipelineStoreError(
            f"Configured Google Sheet tab '{tab_name}' header must include: " + ", ".join(PROCESSOR_REQUIRED_HEADERS)
        )
    duplicates = sorted({column for column in header if header.count(column) > 1})
    if duplicates:
        raise GoogleSheetsPipelineStoreError(
            f"Configured Google Sheet tab '{tab_name}' header has duplicate column(s): " + ", ".join(duplicates)
        )
    return header


def _normalize_row(row: Sequence[str], *, width: int) -> list[str]:
    normalized = [str(value) for value in row[:width]]
    normalized.extend([""] * (width - len(normalized)))
    return normalized


def _row_cell(row: Sequence[str], header: Sequence[str], column: str) -> str:
    try:
        index = tuple(header).index(column)
    except ValueError:
        return ""
    if index >= len(row):
        return ""
    return row[index]


def _processor_local_value(row: Sequence[str], header: Sequence[str]) -> str:
    local_value = _row_cell(row, header, "Local")
    if "Local" in header:
        return local_value
    object_value = _row_cell(row, header, "Object")
    return object_value if Path(object_value).is_absolute() else ""


def _column_name(index: int) -> str:
    if index < 1:
        raise ValueError("column index must be positive")
    name = ""
    value = index
    while value:
        value, remainder = divmod(value - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def _sheet_range(sheet_name: str, coordinates: str) -> str:
    escaped_sheet_name = sheet_name.replace("'", "''")
    return f"'{escaped_sheet_name}'!{coordinates}"


def _row_url(*, spreadsheet_id: str, sheet_id: str, row_number: int, last_column: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        f"#gid={sheet_id}&range=A{row_number}:{last_column}{row_number}"
    )


def _parse_google_row_url(value: str) -> dict[str, JsonValue] | None:
    match = _ROW_URL_RE.search(value)
    if match is None:
        return None
    return {
        "spreadsheet_id": match.group(1),
        "sheet_id": match.group(2),
        "row_number": int(match.group(3)),
    }


def _parse_updated_range_row(value: str) -> int | None:
    match = _UPDATED_RANGE_ROW_RE.search(value)
    return None if match is None else int(match.group(1))


def _visible_source_matches_ref(value: str, ref: ProcessRef) -> bool:
    candidates = {ref.source}
    if ref.row_url is not None:
        candidates.add(ref.row_url)
    if ref.artifact_url is not None:
        candidates.add(ref.artifact_url)
    if ref.artifact_path is not None:
        candidates.add(ref.artifact_path)
    if value in candidates:
        return True
    parsed_value = _parse_google_row_url(value)
    if parsed_value is None:
        return False
    return any(_google_row_urls_match(parsed_value, candidate) for candidate in candidates)


def _google_row_urls_match(parsed_value: Mapping[str, JsonValue], candidate: str) -> bool:
    parsed_candidate = _parse_google_row_url(candidate)
    if parsed_candidate is None:
        return False
    return (
        parsed_value["spreadsheet_id"] == parsed_candidate["spreadsheet_id"]
        and parsed_value["sheet_id"] == parsed_candidate["sheet_id"]
        and parsed_value["row_number"] == parsed_candidate["row_number"]
    )


def _source_ref_from_visible_source(*, stage: str, tab: str, source: str, spreadsheet_id: str) -> ProcessRef:
    parsed = _parse_google_row_url(source)
    return ProcessRef(
        stage=stage,
        tab=tab,
        source=source,
        row_number=None if parsed is None else cast(int, parsed["row_number"]),
        row_url=source if _is_url(source) else None,
        spreadsheet_id=spreadsheet_id,
        sheet_id=None if parsed is None else cast(str, parsed["sheet_id"]),
        artifact_url=source if _is_url(source) and "docs.google.com/spreadsheets" not in source else None,
        artifact_path=source if Path(source).is_absolute() else None,
    )


def _input_stage_for_record_stage(stage: str) -> str:
    if stage == PipelineStage.TEXTIFY.value:
        return "download"
    if stage == PipelineStage.TRANSLATE.value:
        return PipelineStage.TEXTIFY.value
    return stage


def _input_tab_for_record_stage(stage: str, config: PipelineConfig) -> str:
    if stage == PipelineStage.TEXTIFY.value:
        return config.tabs.downloads
    if stage == PipelineStage.TRANSLATE.value:
        return config.tabs.textifications
    return stage


def _download_metadata(row: _DownloadRow) -> JsonObject:
    return {
        "date": row.date,
        "x_date": row.x_date,
        "iMsgX": row.imsgx,
        "source": row.source,
        "column": row.column,
        "type": row.type_,
        "object": row.object_value,
        "downloads_row": row.row_number,
    }


def _already_text_download_text(download: _DownloadRow, *, local_path: Path | None) -> _ExtractedText:
    if local_path is None:
        return _ExtractedText(
            text=download.object_value or download.source,
            source_language_hint=None,
            source="download_object_cell",
        )
    extracted = _text_from_artifact(local_path)
    return _ExtractedText(
        text=extracted.text,
        source_language_hint=extracted.source_language_hint,
        source=f"artifact:{local_path}:{extracted.source}",
    )


def _text_from_artifact(path: Path) -> _ExtractedText:
    raw_text = path.read_text(encoding="utf-8")
    if path.suffix.casefold() == ".json":
        payload = json.loads(raw_text)
        if (payload_mapping := _string_keyed_mapping(payload)) is not None:
            extracted = _text_from_json_mapping(payload_mapping)
            if extracted is not None:
                return extracted
    if path.suffix.casefold() in {".html", ".htm"}:
        return _ExtractedText(
            text=_non_empty_artifact_text(_text_from_html(raw_text), path),
            source_language_hint=None,
            source="html_text",
        )
    return _ExtractedText(
        text=_non_empty_artifact_text(raw_text, path),
        source_language_hint=None,
        source="raw_file",
    )


def _text_from_json_mapping(payload: Mapping[str, object]) -> _ExtractedText | None:
    candidates: list[_ExtractedText] = []
    if (article := _string_keyed_mapping(payload.get("article"))) is not None:
        article_text = _non_empty_json_string(article.get("plain_text"))
        if article_text is not None:
            candidates.append(_ExtractedText(article_text, _json_language_hint(article), "article.plain_text"))
        article_preview_text = _article_preview_text(article)
        if article_preview_text is not None:
            candidates.append(_ExtractedText(article_preview_text, _json_language_hint(article), "article.title_preview_text"))

    plain_text = _non_empty_json_string(payload.get("plain_text"))
    if plain_text is not None:
        candidates.append(_ExtractedText(plain_text, _json_language_hint(payload), "plain_text"))

    for nested_key in ("parent", "quoted_tweet"):
        nested = _string_keyed_mapping(payload.get(nested_key))
        if nested is None:
            continue
        nested_text = _text_from_json_mapping(nested)
        if nested_text is not None:
            candidates.append(
                _ExtractedText(
                    text=nested_text.text,
                    source_language_hint=nested_text.source_language_hint,
                    source=f"{nested_key}.{nested_text.source}",
                )
            )

    candidates.extend(_card_text_candidates(payload))

    text = _non_empty_json_string(payload.get("text"))
    if text is not None:
        candidates.append(_ExtractedText(text, _json_language_hint(payload), "text"))

    if (data := _string_keyed_mapping(payload.get("data"))) is not None:
        data_text = _non_empty_json_string(data.get("text"))
        if data_text is not None:
            candidates.append(_ExtractedText(data_text, _json_language_hint(data), "data.text"))

    content = _non_empty_json_string(payload.get("content"))
    if content is not None:
        candidates.append(_ExtractedText(content, _json_language_hint(payload), "content"))

    return _choose_extracted_text(candidates)


def _article_preview_text(article: Mapping[str, object]) -> str | None:
    title = _non_empty_json_string(article.get("title"))
    preview_text = _non_empty_json_string(article.get("preview_text"))
    if title is None:
        return preview_text
    if preview_text is None:
        return title
    if preview_text.casefold().startswith(title.casefold()):
        return preview_text
    return f"{title}\n\n{preview_text}"


def _string_keyed_mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return cast(Mapping[str, object], value)


def _card_text_candidates(payload: Mapping[str, object]) -> list[_ExtractedText]:
    card = _string_keyed_mapping(payload.get("card"))
    if card is None:
        return []
    binding_values = _string_keyed_mapping(card.get("binding_values"))
    if binding_values is None:
        return []
    candidates: list[_ExtractedText] = []
    for key in (
        "title",
        "description",
        "summary_photo_image_alt_text",
        "photo_image_full_size_alt_text",
        "thumbnail_image_alt_text",
    ):
        value = _string_keyed_mapping(binding_values.get(key))
        if value is None:
            continue
        text = _non_empty_json_string(value.get("string_value"))
        if text is not None:
            candidates.append(_ExtractedText(text, _json_language_hint(payload), f"card.{key}"))
    return candidates


def _choose_extracted_text(candidates: Sequence[_ExtractedText]) -> _ExtractedText | None:
    return next((candidate for candidate in candidates if not _is_url_only_text(candidate.text)), None) or next(
        iter(candidates),
        None,
    )


def _is_url_only_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    return not _URL_ONLY_RE.sub("", stripped).strip()


def _json_language_hint(payload: Mapping[str, object]) -> str | None:
    lang = _non_empty_json_string(payload.get("lang"))
    if lang is not None:
        return normalize_language_hint(lang)
    language = _non_empty_json_string(payload.get("language"))
    if language is not None:
        return normalize_language_hint(language)
    return None


def _non_empty_json_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _non_empty_artifact_text(value: str, path: Path) -> str:
    text = value.strip()
    if not text:
        raise GoogleSheetsPipelineStoreError(f"Already-text download artifact is empty: {path}")
    return text


def _text_from_html(raw_text: str) -> str:
    extractor = _HtmlTextExtractor()
    extractor.feed(raw_text)
    extractor.close()
    return re.sub(r"\s+", " ", " ".join(extractor.parts)).strip()


def _translation_blocks_from_textification_object(object_value: str) -> list[JsonObject]:
    path = Path(object_value).expanduser()
    if not path.is_absolute() or not path.exists():
        return [
            {
                "block_id": 1,
                "name": "textification_object",
                "source_language_hint": None,
                "text": object_value,
                "context": {"object": object_value},
            }
        ]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GoogleSheetsPipelineStoreError(f"Unable to read textification object: {path}") from exc
    if not isinstance(payload, Mapping):
        raise GoogleSheetsPipelineStoreError(f"Textification object must be a JSON object: {path}")
    object_payload = payload.get("object", payload)
    if not isinstance(object_payload, Mapping):
        raise GoogleSheetsPipelineStoreError(f"Textification object payload must be a JSON object: {path}")
    source = object_payload.get("source")
    if not isinstance(source, Mapping):
        raise GoogleSheetsPipelineStoreError(f"Textification object source must be a JSON object: {path}")
    suggested_files = source.get("suggested_files")
    if not isinstance(suggested_files, list) or not suggested_files:
        raise GoogleSheetsPipelineStoreError(f"Textification object has no suggested text files: {path}")
    detected_languages = source.get("detected_languages")
    source_language_hint = None
    if isinstance(detected_languages, list):
        normalized_detected_languages = tuple(
            dict.fromkeys(
                normalized
                for value in detected_languages
                if isinstance(value, str)
                if value.strip()
                if (normalized := normalize_language_hint(value)) is not None
            )
        )
        if len(normalized_detected_languages) == 1:
            source_language_hint = normalized_detected_languages[0]

    blocks: list[JsonObject] = []
    for index, suggested_file in enumerate(suggested_files, start=1):
        if not isinstance(suggested_file, Mapping):
            raise GoogleSheetsPipelineStoreError(f"Textification suggested file must be an object: {path}")
        suggested_file = cast(Mapping[str, object], suggested_file)
        text = suggested_file.get("text")
        if not isinstance(text, str) or not text.strip():
            raise GoogleSheetsPipelineStoreError(f"Textification suggested file text must not be empty: {path}")
        name = suggested_file.get("suggested_path")
        blocks.append(
            {
                "block_id": index,
                "name": name if isinstance(name, str) and name else f"textification_{index}",
                "source_language_hint": source_language_hint,
                "text": text,
                "context": {"textification_object": str(path)},
            }
        )
    return blocks


class _HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in {"noscript", "script", "style", "svg", "template"}:
            self._skip_depth += 1
            return
        if normalized_tag != "meta":
            return
        attr_map = {key.casefold(): value for key, value in attrs if value is not None}
        name = (attr_map.get("name") or attr_map.get("property") or "").casefold()
        if name in {"description", "og:description", "og:title", "twitter:description", "twitter:title"}:
            content = attr_map.get("content")
            if content is not None and content.strip():
                self.parts.append(content.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"noscript", "script", "style", "svg", "template"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        stripped = data.strip()
        if stripped:
            self.parts.append(stripped)


def _legacy_artifact_ref_cell(ref: ArtifactRef | None) -> str:
    if ref is None:
        return ""
    if ref.url is not None:
        return ref.url
    if ref.path is not None:
        return ref.path
    return ""  # pragma: no cover - ArtifactRef validation requires url or path.


def _artifact_url_cell(ref: ArtifactRef | None) -> str:
    return "" if ref is None or ref.url is None else ref.url


def _artifact_path_cell(ref: ArtifactRef | None) -> str:
    return "" if ref is None or ref.path is None else ref.path


def _processor_artifact_path(row: _ProcessorRow) -> str | None:
    return row.local_value if row.local_value and Path(row.local_value).is_absolute() else None


def _artifact_ref_from_processor_row(*, stage: str, row: _ProcessorRow) -> ArtifactRef | None:
    artifact_url = row.object_value if _is_url(row.object_value) else None
    artifact_path = _processor_artifact_path(row)
    if artifact_url is None and artifact_path is None:
        return None
    return ArtifactRef(
        kind=f"{stage}_object",
        mime_type="application/json",
        url=artifact_url,
        path=artifact_path,
    )


def _last_column_for_tab(tab: str, config: PipelineConfig) -> str:
    if tab == config.tabs.imsgx:
        return "I"
    if tab in {config.tabs.textifications, config.tabs.translations}:
        return "H"
    return "G"


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.casefold()).strip("-")
    return slug[:80].strip("-") if slug else "source"
