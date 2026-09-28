from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


def _merge(defaults: dict[str, Any], supplied: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(defaults)
    for key, value in supplied.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


DEFAULTS: dict[str, Any] = {
    "project": {
        "anonymization_salt_env": "ANONYMIZATION_SALT",
        "min_text_length": 3,
        "max_text_length": 10000,
        "vietnamese_only": True,
        "min_vietnamese_score": 0.12,
        "redact_mentions": True,
        "redact_urls": True,
        "redact_emails": True,
        "redact_phones": True,
        "store_permalinks": False,
        "pseudonymize_object_ids": True,
        "store_image_urls": True,
        "max_image_urls": 10,
        "education_keywords": [
            "hoc",
            "hoc tap",
            "sinh vien",
            "hoc sinh",
            "giang vien",
            "giao vien",
            "mon hoc",
            "bai tap",
            "thi",
            "diem",
            "deadline",
            "do an",
            "tin chi",
            "hoc phi",
            "tot nghiep",
            "thuc tap",
        ],
        "education_context_keywords": [
            "truong",
            "dai hoc",
            "cao dang",
            "hoc vien",
            "khoa",
            "lop",
            "sinh vien",
            "hoc sinh",
            "giang vien",
            "giao vien",
            "thay",
            "co",
            "ky tuc xa",
            "ktx",
            "campus",
            "cau lac bo",
            "clb",
            "doan truong",
            "confession truong",
        ],
        "learning_environment_topics": [
            "tinh yeu",
            "crush",
            "yeu tham",
            "hen ho",
            "chia tay",
            "drama",
            "phot",
            "boc phot",
            "xin loi",
            "dinh chinh",
            "mau thuan",
            "cai nhau",
            "bat nat",
            "bao luc hoc duong",
            "quay roi",
            "ap luc",
            "stress",
            "tram cam",
            "co lap",
            "ban be",
            "roommate",
            "mat do",
            "lua dao",
        ],
    },
    "storage": {"state_db": "data/state.sqlite3", "jsonl_dir": "data/runs"},
    "google_sheets": {
        "enabled": True,
        "spreadsheet_id": "1pWQcZkVq_hS0UzITtr5bA9mEb3SPJSYdXBXRpHbzF-k",
        "worksheet": "raw_data",
        "service_account_file_env": "GOOGLE_SERVICE_ACCOUNT_FILE",
        "service_account_json_env": "GOOGLE_SERVICE_ACCOUNT_JSON",
        "batch_size": 200,
    },
    "facebook": {"enabled": False, "terms_acknowledged": False, "pages": []},
    "threads": {"enabled": False, "terms_acknowledged": False, "queries": []},
    "reddit": {"enabled": False, "terms_acknowledged": False, "subreddits": []},
}


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Khong tim thay file cau hinh: {path}")
    with path.open("r", encoding="utf-8") as handle:
        supplied = yaml.safe_load(handle) or {}
    if not isinstance(supplied, dict):
        raise ConfigError("Cau hinh YAML phai la mot object/map.")
    config = _merge(DEFAULTS, supplied)
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    sheet = config["google_sheets"]
    if sheet.get("enabled") and not str(sheet.get("spreadsheet_id", "")).strip():
        raise ConfigError("google_sheets.spreadsheet_id khong duoc de trong.")
    if sheet.get("enabled") and not str(sheet.get("worksheet", "")).strip():
        raise ConfigError("google_sheets.worksheet khong duoc de trong.")

    for platform in ("facebook", "threads", "reddit"):
        section = config[platform]
        if section.get("enabled") and not section.get("terms_acknowledged"):
            raise ConfigError(
                f"{platform}.terms_acknowledged phai la true sau khi ban da kiem tra "
                "quyen truy cap va quyen su dung du lieu."
            )

    pages = config["facebook"].get("pages", [])
    if not isinstance(pages, list):
        raise ConfigError("facebook.pages phai la danh sach.")
    for page in pages:
        if not isinstance(page, dict) or not page.get("id"):
            raise ConfigError("Moi facebook.pages item can co id.")

    if config["project"]["min_text_length"] < 1:
        raise ConfigError("project.min_text_length phai >= 1.")
