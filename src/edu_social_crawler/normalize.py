from __future__ import annotations

import hashlib
import hmac
import html
import json
import re
import unicodedata
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from .models import CleanRecord, RawItem

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[ .-]?\d){8,10}(?!\d)")
MENTION_RE = re.compile(r"(?<!\w)@[\w.]{2,64}", flags=re.UNICODE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SPACE_RE = re.compile(r"[^\S\n]+")
NEWLINES_RE = re.compile(r"\n{3,}")
VI_CHARS_RE = re.compile(
    r"[ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệ"
    r"íìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]",
    re.IGNORECASE,
)
VI_WORDS = {
    "mình",
    "bạn",
    "các",
    "được",
    "không",
    "với",
    "cho",
    "học",
    "sinh",
    "viên",
    "trường",
    "lớp",
    "thầy",
    "cô",
    "thi",
    "điểm",
    "bài",
    "môn",
}


def normalize_text(text: str | None, rules: dict[str, Any]) -> str:
    if not text:
        return ""
    value = unicodedata.normalize("NFC", html.unescape(str(text)))
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = CONTROL_RE.sub("", value)
    if rules.get("redact_urls", True):
        value = URL_RE.sub("[URL]", value)
    if rules.get("redact_emails", True):
        value = EMAIL_RE.sub("[EMAIL]", value)
    if rules.get("redact_phones", True):
        value = PHONE_RE.sub("[PHONE]", value)
    if rules.get("redact_mentions", True):
        value = MENTION_RE.sub("[USER]", value)
    value = "\n".join(SPACE_RE.sub(" ", line).strip() for line in value.split("\n"))
    return NEWLINES_RE.sub("\n\n", value).strip()


def vietnamese_score(text: str) -> float:
    words = re.findall(r"\b\w+\b", text.casefold(), flags=re.UNICODE)
    if not words:
        return 0.0
    stopword_hits = sum(word in VI_WORDS for word in words)
    diacritic_hits = len(VI_CHARS_RE.findall(text))
    return min(1.0, (stopword_hits * 2 + diacritic_hits) / max(8, len(words)))


def education_relevance(item: RawItem, texts: list[str], keywords: list[str]) -> float:
    return education_environment_relevance(item, texts, keywords, [], [])


def _search_key(value: str) -> str:
    value = value.casefold().replace("đ", "d")
    return "".join(
        character
        for character in unicodedata.normalize("NFD", value)
        if unicodedata.category(character) != "Mn"
    )


def _keyword_hits(haystack: str, keywords: list[str]) -> int:
    hits = 0
    for keyword in keywords:
        normalized = _search_key(str(keyword)).strip()
        if not normalized:
            continue
        pattern = re.escape(normalized).replace(r"\ ", r"\s+")
        if re.search(rf"(?<!\w){pattern}(?!\w)", haystack):
            hits += 1
    return hits


def education_environment_relevance(
    item: RawItem,
    texts: list[str],
    academic_keywords: list[str],
    context_keywords: list[str],
    environment_topics: list[str],
) -> float:
    if item.trusted_education_source:
        return 1.0
    haystack = _search_key(" ".join([item.source_name, *texts]))
    academic_hits = _keyword_hits(haystack, academic_keywords)
    context_hits = _keyword_hits(haystack, context_keywords)
    topic_hits = _keyword_hits(haystack, environment_topics)
    if academic_hits:
        return round(min(1.0, 0.4 + academic_hits * 0.15), 4)
    if context_hits and topic_hits:
        return round(min(1.0, 0.45 + context_hits * 0.1 + topic_hits * 0.1), 4)
    return 0.0


def normalize_image_urls(urls: list[str], maximum: int = 10) -> str:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_url in urls:
        url = html.unescape(str(raw_url)).strip()
        try:
            scheme = urlsplit(url).scheme.casefold()
        except ValueError:
            continue
        if scheme not in {"http", "https"} or url in seen:
            continue
        normalized.append(url)
        seen.add(url)
        if len(normalized) >= maximum:
            break
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))


def anonymize_author(platform: str, author_id: str, salt: str) -> str:
    if not author_id:
        return ""
    digest = hmac.new(
        salt.encode("utf-8"),
        f"{platform}:{author_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"anon_{digest[:20]}"


def pseudonymize_object_id(platform: str, kind: str, value: str, salt: str) -> str:
    if not value:
        return ""
    digest = hmac.new(
        salt.encode("utf-8"),
        f"{platform}:{kind}:{value}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"obj_{digest[:24]}"


def clean_item(
    item: RawItem,
    project_config: dict[str, Any],
    salt: str,
    run_id: str,
) -> CleanRecord | None:
    target = normalize_text(item.target_text, project_config)
    post = normalize_text(item.post_text, project_config)
    parent = normalize_text(item.parent_comment_text, project_config)
    min_length = int(project_config.get("min_text_length", 3))
    max_length = int(project_config.get("max_text_length", 10000))
    if len(target) < min_length or len(target) > max_length:
        return None
    if target.casefold() in {"[deleted]", "[removed]", "deleted", "removed"}:
        return None

    score = vietnamese_score(" ".join([post, parent, target]))
    if project_config.get("vietnamese_only", True) and score < float(
        project_config.get("min_vietnamese_score", 0.12)
    ):
        return None
    language = "vi" if score >= 0.12 else "mixed_or_unknown"

    relevance = education_environment_relevance(
        item,
        [post, parent, target],
        list(project_config.get("education_keywords", [])),
        list(project_config.get("education_context_keywords", [])),
        list(project_config.get("learning_environment_topics", [])),
    )
    if relevance <= 0:
        return None

    content_hash = hmac.new(
        salt.encode("utf-8"),
        "\x1f".join([item.platform, post, parent, target]).encode(),
        hashlib.sha256,
    ).hexdigest()
    if project_config.get("pseudonymize_object_ids", True):
        source_item_id = pseudonymize_object_id(
            item.platform, "source_item", item.source_item_id, salt
        )
        post_id = pseudonymize_object_id(item.platform, "post", item.post_id, salt)
        parent_comment_id = pseudonymize_object_id(
            item.platform, "comment", item.parent_comment_id, salt
        )
    else:
        source_item_id = item.source_item_id
        post_id = item.post_id
        parent_comment_id = item.parent_comment_id
    return CleanRecord(
        collected_at=datetime.now(UTC).isoformat(),
        platform=item.platform,
        source_name=normalize_text(item.source_name, {"redact_mentions": False}),
        source_type=item.source_type,
        object_type=item.object_type,
        source_item_id=source_item_id,
        post_id=post_id,
        parent_comment_id=parent_comment_id,
        post_text=post,
        parent_comment_text=parent,
        target_text=target,
        permalink=item.permalink if project_config.get("store_permalinks", False) else "",
        published_at=item.published_at,
        language=language,
        education_relevance=relevance,
        author_hash=anonymize_author(item.platform, item.author_id, salt),
        content_hash=content_hash,
        collection_run_id=run_id,
        image_urls=(
            normalize_image_urls(
                item.image_urls,
                max(1, int(project_config.get("max_image_urls", 10))),
            )
            if project_config.get("store_image_urls", True)
            else "[]"
        ),
    )
