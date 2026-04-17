"""config_loader.py 단위 테스트."""

from pathlib import Path

import pytest
import yaml

from f2md.config_loader import get_path, load_config


@pytest.fixture
def mock_project(tmp_path) -> Path:
    """임시 프로젝트 구조와 settings.yaml을 생성한다."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    settings = {
        "paths": {
            "input": "input",
            "raw_md": "output/raw_md",
            "clean_md": "output/clean_md",
            "json_logs": "output/json_logs",
            "failed": "output/failed",
        },
        "modes": {
            "default": "standard",
            "chain": ["standard", "ocr", "high_accuracy"],
        },
        "validation": {
            "min_char_count": 50,
        },
    }
    (config_dir / "settings.yaml").write_text(
        yaml.dump(settings, allow_unicode=True),
        encoding="utf-8",
    )
    return tmp_path


class TestLoadConfig:
    def test_loads_yaml_successfully(self, mock_project):
        cfg = load_config(mock_project)
        assert isinstance(cfg, dict)

    def test_paths_are_absolute(self, mock_project):
        cfg = load_config(mock_project)
        for key, path in cfg["paths"].items():
            assert isinstance(path, Path), f"paths.{key}가 Path 객체가 아님"
            assert path.is_absolute(), f"paths.{key}가 절대 경로가 아님"

    def test_raw_md_path_correct(self, mock_project):
        cfg = load_config(mock_project)
        assert cfg["paths"]["raw_md"] == (mock_project / "output" / "raw_md").resolve()

    def test_root_key_set(self, mock_project):
        cfg = load_config(mock_project)
        assert "_root" in cfg
        assert cfg["_root"] == mock_project.resolve()

    def test_missing_config_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path)

    def test_validation_section_preserved(self, mock_project):
        cfg = load_config(mock_project)
        assert cfg["validation"]["min_char_count"] == 50


class TestGetPath:
    def test_returns_path_object(self, mock_project):
        cfg = load_config(mock_project)
        p = get_path(cfg, "raw_md")
        assert isinstance(p, Path)

    def test_key_error_for_missing_key(self, mock_project):
        cfg = load_config(mock_project)
        with pytest.raises(KeyError):
            get_path(cfg, "nonexistent_key")
