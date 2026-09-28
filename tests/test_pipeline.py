from pathlib import Path

from edu_social_crawler.models import RawItem
from edu_social_crawler.pipeline import run_collection


class FakeProvider:
    def collect(self):
        yield RawItem(
            platform="threads",
            source_name="học tập",
            source_type="keyword_search",
            object_type="post",
            source_item_id="post-1",
            target_text="Mình đang học bài 😄",
            trusted_education_source=True,
        )


def test_dry_run_does_not_create_state_database(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TEST_ANON_SALT", "a-very-long-test-salt")
    state_path = tmp_path / "state.sqlite3"
    config = {
        "project": {
            "anonymization_salt_env": "TEST_ANON_SALT",
            "min_text_length": 3,
            "max_text_length": 10000,
            "vietnamese_only": True,
            "min_vietnamese_score": 0.05,
            "education_keywords": ["học"],
        },
        "storage": {
            "state_db": str(state_path),
            "jsonl_dir": str(tmp_path / "runs"),
        },
    }

    result = run_collection(config, [FakeProvider()], dry_run=True)  # type: ignore[list-item]

    assert result["accepted"] == 1
    assert not state_path.exists()
    assert Path(str(result["output"])).read_text(encoding="utf-8").count("\n") == 1
