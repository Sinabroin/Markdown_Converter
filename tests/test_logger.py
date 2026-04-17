"""logger.py 단위 테스트."""

import json
from pathlib import Path

from f2md.logger import build_log, get_markitdown_version, write_log


class TestWriteLog:
    def test_creates_json_file(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_data = {
            "input_file": "test.pdf",
            "status": "success",
        }
        log_path = write_log(log_dir, log_data)

        assert log_path.exists()
        assert log_path.suffix == ".json"

    def test_log_filename_based_on_stem(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_data = {"input_file": "my_document.pdf", "status": "success"}
        log_path = write_log(log_dir, log_data)

        assert log_path.name == "my_document.json"

    def test_log_contains_timestamp(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_data = {"input_file": "test.pdf", "status": "success"}
        log_path = write_log(log_dir, log_data)

        content = json.loads(log_path.read_text(encoding="utf-8"))
        assert "timestamp" in content
        assert "python_version" in content

    def test_log_is_valid_json(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_data = {"input_file": "test.pdf", "status": "success", "extra": None}
        log_path = write_log(log_dir, log_data)

        content = json.loads(log_path.read_text(encoding="utf-8"))
        assert content["status"] == "success"

    def test_creates_log_dir_if_not_exists(self, tmp_path):
        log_dir = tmp_path / "non_existent" / "logs"
        assert not log_dir.exists()
        write_log(log_dir, {"input_file": "x.pdf", "status": "success"})
        assert log_dir.exists()

    def test_original_data_not_mutated(self, tmp_path):
        log_dir = tmp_path / "logs"
        original = {"input_file": "test.pdf", "status": "success"}
        original_copy = dict(original)
        write_log(log_dir, original)
        assert original == original_copy


class TestBuildLog:
    def test_build_log_returns_dict(self):
        log = build_log(
            input_file="test.pdf",
            input_size_bytes=1024,
            detected_type=".pdf",
            selected_mode="standard",
            escalated_to=None,
            retry_count=0,
            markitdown_version="0.1.0",
            output_raw="output/raw_md/test.md",
            output_clean="output/clean_md/test.md",
            validation={"passed": True, "char_count": 500},
            duration_seconds=1.23,
            status="success",
        )
        assert isinstance(log, dict)
        assert log["status"] == "success"
        assert log["input_file"] == "test.pdf"
        assert log["retry_count"] == 0
        assert log["duration_seconds"] == 1.23

    def test_error_field_defaults_to_none(self):
        log = build_log(
            input_file="test.pdf",
            input_size_bytes=1024,
            detected_type=".pdf",
            selected_mode="standard",
            escalated_to=None,
            retry_count=0,
            markitdown_version="0.1.0",
            output_raw=None,
            output_clean=None,
            validation={},
            duration_seconds=0.5,
            status="failed",
        )
        assert log["error"] is None


class TestGetMarkitdownVersion:
    def test_returns_string(self):
        version = get_markitdown_version()
        assert isinstance(version, str)
        assert len(version) > 0
