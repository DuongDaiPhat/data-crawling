from __future__ import annotations

import json
import os
from collections.abc import Iterable
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .normalize import clean_item
from .providers import FacebookProvider, Provider, RedditProvider, ThreadsProvider
from .sheets import GoogleSheetsSink
from .state import StateStore

PROVIDERS: dict[str, type[Provider]] = {
    "facebook": FacebookProvider,
    "threads": ThreadsProvider,
    "reddit": RedditProvider,
}


def build_providers(config: dict[str, Any], selected: Iterable[str]) -> list[Provider]:
    result: list[Provider] = []
    for name in selected:
        section = config[name]
        if not section.get("enabled"):
            continue
        result.append(PROVIDERS[name](section))
    return result


def run_collection(
    config: dict[str, Any],
    providers: list[Provider],
    dry_run: bool = False,
) -> dict[str, int | str]:
    project = config["project"]
    salt_env = str(project.get("anonymization_salt_env", "ANONYMIZATION_SALT"))
    salt = os.environ.get(salt_env, "")
    if not salt or len(salt) < 16:
        raise ValueError(f"{salt_env} phai co it nhat 16 ky tu de an danh on dinh.")

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(config["storage"]["jsonl_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{run_id}.jsonl"
    counts: dict[str, int | str] = {
        "raw": 0,
        "accepted": 0,
        "duplicate": 0,
        "filtered": 0,
        "output": str(output_path),
    }
    state_path = Path(config["storage"]["state_db"])
    state_context = nullcontext(None) if dry_run else StateStore(state_path)
    with state_context as state, output_path.open("w", encoding="utf-8") as handle:
        for provider in providers:
            for item in provider.collect():
                counts["raw"] = int(counts["raw"]) + 1
                record = clean_item(item, project, salt, run_id)
                if record is None:
                    counts["filtered"] = int(counts["filtered"]) + 1
                    continue
                if state is None:
                    handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
                    counts["accepted"] = int(counts["accepted"]) + 1
                    continue
                if not state.add(record):
                    counts["duplicate"] = int(counts["duplicate"]) + 1
                    continue
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
                counts["accepted"] = int(counts["accepted"]) + 1
    return counts


def sync_pending(config: dict[str, Any]) -> dict[str, int]:
    sheet_config = config["google_sheets"]
    if not sheet_config.get("enabled"):
        return {"synced": 0, "remaining": 0}
    batch_size = int(sheet_config.get("batch_size", 200))
    sink = GoogleSheetsSink(sheet_config)
    synced = 0
    with StateStore(Path(config["storage"]["state_db"])) as state:
        while True:
            batch = state.pending(batch_size)
            if not batch:
                break
            sink.append([record for _, record in batch])
            state.mark_synced([row_id for row_id, _ in batch])
            synced += len(batch)
        remaining = state.counts()["pending"]
    return {"synced": synced, "remaining": remaining}
