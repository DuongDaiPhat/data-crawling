from pathlib import Path

from edu_social_crawler.models import CleanRecord
from edu_social_crawler.state import StateStore


def sample_record() -> CleanRecord:
    return CleanRecord(
        collected_at="2026-01-01T00:00:00+00:00",
        platform="reddit",
        source_name="r/test",
        source_type="public_subreddit",
        object_type="comment",
        source_item_id="abc",
        post_id="post",
        parent_comment_id="",
        post_text="Bài đăng",
        parent_comment_text="",
        target_text="Mình đang học 😄",
        permalink="https://example.test",
        published_at="",
        language="vi",
        education_relevance=1.0,
        author_hash="anon_123",
        content_hash="hash",
        collection_run_id="run",
        image_urls="[]",
    )


def test_pending_records_survive_until_marked_synced(tmp_path: Path) -> None:
    with StateStore(tmp_path / "state.sqlite3") as state:
        record = sample_record()
        assert state.add(record) is True
        assert state.add(record) is False
        pending = state.pending(100)
        assert len(pending) == 1
        state.mark_synced([pending[0][0]])
        assert state.counts() == {"pending": 0, "synced": 1}
