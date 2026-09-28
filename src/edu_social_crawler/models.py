from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

SHEET_HEADERS = [
    "collected_at",
    "platform",
    "source_name",
    "source_type",
    "object_type",
    "source_item_id",
    "post_id",
    "parent_comment_id",
    "post_text",
    "parent_comment_text",
    "target_text",
    "permalink",
    "published_at",
    "language",
    "education_relevance",
    "author_hash",
    "content_hash",
    "collection_run_id",
    "image_urls",
]


@dataclass(slots=True)
class RawItem:
    platform: str
    source_name: str
    source_type: str
    object_type: str
    source_item_id: str
    target_text: str
    post_id: str = ""
    parent_comment_id: str = ""
    post_text: str = ""
    parent_comment_text: str = ""
    permalink: str = ""
    published_at: str = ""
    author_id: str = ""
    trusted_education_source: bool = False
    image_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CleanRecord:
    collected_at: str
    platform: str
    source_name: str
    source_type: str
    object_type: str
    source_item_id: str
    post_id: str
    parent_comment_id: str
    post_text: str
    parent_comment_text: str
    target_text: str
    permalink: str
    published_at: str
    language: str
    education_relevance: float
    author_hash: str
    content_hash: str
    collection_run_id: str
    image_urls: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_sheet_row(self) -> list[Any]:
        data = self.to_dict()
        return [data[header] for header in SHEET_HEADERS]

    def image_url_list(self) -> list[str]:
        if not self.image_urls:
            return []
        parsed = json.loads(self.image_urls)
        return [str(value) for value in parsed] if isinstance(parsed, list) else []

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CleanRecord:
        return cls(**{key: data.get(key, "") for key in SHEET_HEADERS})
