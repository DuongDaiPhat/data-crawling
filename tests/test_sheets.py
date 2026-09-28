from edu_social_crawler.models import SHEET_HEADERS
from edu_social_crawler.sheets import LEGACY_SHEET_HEADERS, GoogleSheetsSink


class FakeWorksheet:
    def __init__(self) -> None:
        self.col_count = len(LEGACY_SHEET_HEADERS)
        self.added_columns = 0
        self.updates = []
        self.url = "https://docs.google.com/spreadsheets/d/test/edit#gid=1"

    def row_values(self, row: int):
        assert row == 1
        return LEGACY_SHEET_HEADERS.copy()

    def add_cols(self, count: int) -> None:
        self.added_columns += count
        self.col_count += count

    def update(self, **kwargs) -> None:
        self.updates.append(kwargs)


class FakeSpreadsheet:
    def __init__(self, worksheet: FakeWorksheet) -> None:
        self._worksheet = worksheet

    def worksheet(self, title: str):
        assert title == "raw_data"
        return self._worksheet


class FakeClient:
    def __init__(self, worksheet: FakeWorksheet) -> None:
        self._worksheet = worksheet

    def open_by_key(self, spreadsheet_id: str):
        assert spreadsheet_id == "sheet-id"
        return FakeSpreadsheet(self._worksheet)


def test_legacy_sheet_header_is_extended_without_shifting_columns(monkeypatch) -> None:
    worksheet = FakeWorksheet()
    monkeypatch.setattr(
        "edu_social_crawler.sheets.gspread.authorize", lambda _: FakeClient(worksheet)
    )
    monkeypatch.setattr(GoogleSheetsSink, "_credentials", lambda _: object())
    sink = GoogleSheetsSink({"spreadsheet_id": "sheet-id", "worksheet": "raw_data"})

    assert sink.verify() == worksheet.url
    assert worksheet.added_columns == 1
    assert worksheet.updates == [
        {
            "values": [["image_urls"]],
            "range_name": f"{chr(64 + len(SHEET_HEADERS))}1",
            "raw": True,
        }
    ]
