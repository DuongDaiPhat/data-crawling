from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from .models import CleanRecord


class StateStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                source_item_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                synced_at TEXT,
                UNIQUE(platform, source_item_id)
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_records_status ON records(status, id)"
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def add(self, record: CleanRecord) -> bool:
        try:
            self.connection.execute(
                """
                INSERT INTO records (
                    platform, source_item_id, content_hash, payload_json, status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (
                    record.platform,
                    record.source_item_id,
                    record.content_hash,
                    json.dumps(record.to_dict(), ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def pending(self, limit: int) -> list[tuple[int, CleanRecord]]:
        rows = self.connection.execute(
            "SELECT id, payload_json FROM records WHERE status = 'pending' ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            (int(row["id"]), CleanRecord.from_dict(json.loads(row["payload_json"]))) for row in rows
        ]

    def mark_synced(self, ids: Iterable[int]) -> None:
        values = [(datetime.now(UTC).isoformat(), int(row_id)) for row_id in ids]
        self.connection.executemany(
            "UPDATE records SET status = 'synced', synced_at = ? WHERE id = ?",
            values,
        )
        self.connection.commit()

    def counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT status, COUNT(*) AS count FROM records GROUP BY status"
        ).fetchall()
        result = {"pending": 0, "synced": 0}
        result.update({str(row["status"]): int(row["count"]) for row in rows})
        return result

    def __enter__(self) -> StateStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
