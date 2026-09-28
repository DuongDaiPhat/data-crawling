from edu_social_crawler.models import RawItem
from edu_social_crawler.normalize import (
    anonymize_author,
    clean_item,
    normalize_image_urls,
    normalize_text,
)

RULES = {
    "redact_urls": True,
    "redact_emails": True,
    "redact_phones": True,
    "redact_mentions": True,
}


def test_normalize_preserves_emoji_and_redacts_pii() -> None:
    raw = "  Chào  @ban nhé 😭🔥 https://example.com\r\n0901 234 567  "
    result = normalize_text(raw, RULES)
    assert "😭🔥" in result
    assert "@ban" not in result
    assert "https://" not in result
    assert "0901" not in result
    assert result == "Chào [USER] nhé 😭🔥 [URL]\n[PHONE]"


def test_author_hash_is_stable_and_platform_scoped() -> None:
    first = anonymize_author("facebook", "123", "a-very-long-test-salt")
    second = anonymize_author("facebook", "123", "a-very-long-test-salt")
    other = anonymize_author("reddit", "123", "a-very-long-test-salt")
    assert first == second
    assert first != other
    assert first.startswith("anon_")


def test_clean_item_keeps_context() -> None:
    item = RawItem(
        platform="facebook",
        source_name="Confession trường ABC",
        source_type="public_page",
        object_type="reply",
        source_item_id="c2",
        post_id="p1",
        parent_comment_id="c1",
        post_text="Thông báo lịch thi học kỳ",
        parent_comment_text="Môn này khó không bạn?",
        target_text="Mình lo quá 😭 nhưng vẫn cố học",
        author_id="user-1",
        trusted_education_source=True,
        image_urls=["https://img.example/post.jpg", "javascript:alert(1)"],
    )
    project = {
        **RULES,
        "min_text_length": 3,
        "max_text_length": 10000,
        "vietnamese_only": True,
        "min_vietnamese_score": 0.05,
        "education_keywords": ["học", "thi"],
    }
    record = clean_item(item, project, "a-very-long-test-salt", "run-1")
    assert record is not None
    assert record.post_text == "Thông báo lịch thi học kỳ"
    assert record.parent_comment_text == "Môn này khó không bạn?"
    assert "😭" in record.target_text
    assert record.author_hash.startswith("anon_")
    assert record.source_item_id.startswith("obj_")
    assert record.post_id.startswith("obj_")
    assert record.permalink == ""
    assert record.image_url_list() == ["https://img.example/post.jpg"]


def test_school_environment_topic_is_accepted_with_context() -> None:
    item = RawItem(
        platform="threads",
        source_name="Confession trường ABC",
        source_type="keyword_search",
        object_type="post",
        source_item_id="t1",
        target_text="Drama tình yêu trong trường làm mình stress quá 😭",
        trusted_education_source=False,
    )
    project = {
        **RULES,
        "min_text_length": 3,
        "max_text_length": 10000,
        "vietnamese_only": True,
        "min_vietnamese_score": 0.05,
        "education_keywords": ["học tập", "thi"],
        "education_context_keywords": ["trường", "sinh viên"],
        "learning_environment_topics": ["tình yêu", "drama", "stress"],
    }

    record = clean_item(item, project, "a-very-long-test-salt", "run-1")

    assert record is not None
    assert record.education_relevance > 0


def test_environment_topic_without_school_context_is_rejected() -> None:
    item = RawItem(
        platform="threads",
        source_name="Trang giải trí",
        source_type="keyword_search",
        object_type="post",
        source_item_id="t2",
        target_text="Drama tình yêu của người nổi tiếng",
        trusted_education_source=False,
    )
    project = {
        **RULES,
        "min_text_length": 3,
        "max_text_length": 10000,
        "vietnamese_only": False,
        "education_keywords": ["học tập", "thi"],
        "education_context_keywords": ["trường", "sinh viên"],
        "learning_environment_topics": ["tình yêu", "drama"],
    }

    assert clean_item(item, project, "a-very-long-test-salt", "run-1") is None


def test_image_urls_are_deduplicated_and_http_only() -> None:
    result = normalize_image_urls(
        [
            "https://img.example/a.jpg?x=1&amp;y=2",
            "https://img.example/a.jpg?x=1&y=2",
            "ftp://img.example/b.jpg",
        ]
    )
    assert result == '["https://img.example/a.jpg?x=1&y=2"]'
