from __future__ import annotations

import json
import os
from typing import Any

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

from .models import SHEET_HEADERS, CleanRecord

LEGACY_SHEET_HEADERS = SHEET_HEADERS[:-1]


class SheetError(RuntimeError):
    pass


class GoogleSheetsSink:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._worksheet_cache: gspread.Worksheet | None = None

    def _credentials(self) -> Credentials:
        file_env = str(self.config.get("service_account_file_env", ""))
        json_env = str(self.config.get("service_account_json_env", ""))
        file_path = os.environ.get(file_env) if file_env else None
        json_value = os.environ.get(json_env) if json_env else None
        if file_path:
            if not os.path.exists(file_path):
                raise SheetError(f"Khong tim thay service account file: {file_path}")
            return Credentials.from_service_account_file(file_path, scopes=self.SCOPES)
        if json_value:
            try:
                info = json.loads(json_value)
            except json.JSONDecodeError as exc:
                raise SheetError(f"{json_env} khong phai JSON hop le.") from exc
            return Credentials.from_service_account_info(info, scopes=self.SCOPES)
        raise SheetError(
            f"Can dat {file_env} (duong dan file JSON) hoac {json_env} (noi dung JSON)."
        )

    def _worksheet(self) -> gspread.Worksheet:
        if self._worksheet_cache is not None:
            return self._worksheet_cache
        client = gspread.authorize(self._credentials())
        try:
            spreadsheet = client.open_by_key(str(self.config["spreadsheet_id"]))
        except gspread.exceptions.APIError as exc:
            raise SheetError(
                "Khong mo duoc Google Sheet. Hay share Sheet voi client_email cua service account."
            ) from exc
        title = str(self.config["worksheet"])
        try:
            worksheet = spreadsheet.worksheet(title)
        except WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=title,
                rows=1000,
                cols=len(SHEET_HEADERS),
            )
        current_headers = worksheet.row_values(1)
        if not current_headers:
            if worksheet.col_count < len(SHEET_HEADERS):
                worksheet.add_cols(len(SHEET_HEADERS) - worksheet.col_count)
            worksheet.update(values=[SHEET_HEADERS], range_name="A1", raw=True)
        elif current_headers[: len(SHEET_HEADERS)] == SHEET_HEADERS:
            pass
        elif current_headers == LEGACY_SHEET_HEADERS:
            if worksheet.col_count < len(SHEET_HEADERS):
                worksheet.add_cols(len(SHEET_HEADERS) - worksheet.col_count)
            column = _column_letter(len(SHEET_HEADERS))
            worksheet.update(values=[[SHEET_HEADERS[-1]]], range_name=f"{column}1", raw=True)
        else:
            raise SheetError(
                f"Header tab '{title}' khong dung schema. De an toan, hay doi worksheet "
                "trong config hoac sua header theo README."
            )
        self._worksheet_cache = worksheet
        return worksheet

    def verify(self) -> str:
        worksheet = self._worksheet()
        return worksheet.url

    def append(self, records: list[CleanRecord]) -> None:
        if not records:
            return
        worksheet = self._worksheet()
        worksheet.append_rows(
            [record.to_sheet_row() for record in records],
            value_input_option="RAW",
            insert_data_option="INSERT_ROWS",
            table_range=f"A:{_column_letter(len(SHEET_HEADERS))}",
        )


def _column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result
