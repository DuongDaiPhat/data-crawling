from pathlib import Path

import pytest

from edu_social_crawler.config import ConfigError, load_config


def test_enabled_provider_requires_terms_acknowledgement(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("facebook:\n  enabled: true\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="terms_acknowledged"):
        load_config(path)


def test_minimal_disabled_config_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("{}\n", encoding="utf-8")
    config = load_config(path)
    assert config["google_sheets"]["spreadsheet_id"].startswith("1pWQc")
