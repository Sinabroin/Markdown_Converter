"""Different files with identical basenames must have distinct output keys."""

from pathlib import Path

from f2md.logger import write_log
from scripts.convert_batch import run_batch


def test_batch_files_with_same_stem_get_unique_keys(monkeypatch, tmp_path, cfg):
    base = tmp_path / "input"
    base.mkdir()
    (base / "report.pdf").write_bytes(b"placeholder")
    (base / "report.docx").write_bytes(b"placeholder")
    nested = base / "nested"
    nested.mkdir()
    (nested / "report.pdf").write_bytes(b"placeholder")
    (base / "unique.txt").write_text("unique", encoding="utf-8")
    captured = {}

    def fake_convert_one(input_path: Path, config, force=False, output_key=None):
        captured[input_path.relative_to(base).as_posix()] = output_key
        return {"status": "success", "error": None}

    monkeypatch.setattr("scripts.convert_batch.convert_one", fake_convert_one)
    result = run_batch(base, cfg, recursive=True, max_workers=2)
    assert result["total"] == result["success"] == 4
    keys = [
        captured["report.pdf"],
        captured["report.docx"],
        captured["nested/report.pdf"],
    ]
    assert all(key.startswith("report__") for key in keys)
    assert len(set(keys)) == 3
    assert captured["unique.txt"] is None


def test_logger_override_keeps_collision_logs(tmp_path):
    log_dir = tmp_path / "logs"
    path_a = write_log(log_dir, {"input_file": "report.pdf"}, stem_override="report__pdf__abc")
    path_b = write_log(log_dir, {"input_file": "report.docx"}, stem_override="report__docx__xyz")
    assert path_a != path_b
    assert path_a.exists() and path_b.exists()


def test_single_file_output_key_preserves_unique_filename(monkeypatch, tmp_path, cfg):
    from scripts.convert_one import convert_one

    doc = tmp_path / "report.txt"
    doc.write_text("Example input" * 30, encoding="utf-8")

    class StubExtractor:
        def __init__(self, mode, cfg=None):
            pass

        def extract(self, source):
            return "# Test\n\n" + "Distinct content is available for extraction. " * 2, None

    monkeypatch.setattr("scripts.convert_one.extractor.Extractor", StubExtractor)
    cfg["modes"]["chain"] = ["standard"]
    result = convert_one(doc, cfg, output_key="report__txt__fixed")
    assert result["status"] == "success"
    assert (cfg["paths"]["raw_md"] / "report__txt__fixed.md").exists()
    assert (cfg["paths"]["clean_md"] / "report__txt__fixed.md").exists()
    assert (cfg["paths"]["json_logs"] / "report__txt__fixed.json").exists()
