"""Regression tests for the local-first cloud processing guard."""

import pytest

from f2md.extractor import Extractor
from scripts.convert_one import convert_one


@pytest.mark.parametrize("mode", ["ocr", "high_accuracy"])
def test_cloud_extractor_requires_opt_in(mode):
    with pytest.raises(PermissionError, match="Cloud mode"):
        Extractor(mode=mode)


@pytest.mark.parametrize("mode", ["ocr", "high_accuracy"])
def test_cloud_extractor_respects_explicit_disable(mode):
    with pytest.raises(PermissionError, match="Cloud mode"):
        Extractor(mode=mode, cfg={"security": {"allow_cloud_processing": False}})


@pytest.mark.parametrize("mode", ["ocr", "high_accuracy"])
def test_convert_one_rejects_cloud_initial_mode(tmp_path, cfg, mode):
    source = tmp_path / "document.pdf"
    source.write_bytes(b"%PDF-1.4 test fixture")

    with pytest.raises(PermissionError, match="Cloud processing is disabled"):
        convert_one(source, cfg, initial_mode=mode)

    assert not (tmp_path / "output").exists()


def test_local_processing_filters_cloud_escalations(monkeypatch, tmp_path, cfg):
    """If local extraction fails, cloud extractors must never be initialized."""
    source = tmp_path / "document.txt"
    source.write_text("ordinary local content", encoding="utf-8")

    cfg["modes"]["chain"] = ["standard", "paddle_ocr", "ocr", "high_accuracy"]
    modes_seen = []

    class FakeExtractor:
        def __init__(self, mode, cfg=None):
            modes_seen.append(mode)
            if mode in {"ocr", "high_accuracy"}:
                raise AssertionError("unexpected cloud mode")

        def extract(self, path):
            raise RuntimeError("simulated extraction failure")

    monkeypatch.setattr("scripts.convert_one.extractor.Extractor", FakeExtractor)
    result = convert_one(source, cfg)

    assert result["status"] == "failed"
    assert modes_seen == ["standard", "paddle_ocr"]


def test_settings_disable_cloud_by_default():
    from f2md.config_loader import load_config

    cfg = load_config()
    assert cfg["security"]["allow_cloud_processing"] is False
