"""OCR integration compatibility tests using synthetic engine fakes.

No external documents, model downloads, or real OCR models are needed.
"""

import sys
from types import SimpleNamespace

import pytest

from f2md.extractor import Extractor


class FakeOCRv3:
    seen = []

    def __init__(self, **kwargs):
        self.options = kwargs

    def predict(self, path):
        self.seen.append(path)
        if path.lower().endswith(".pdf"):
            return [
                {"res": {"rec_texts": ["Page one", "Korean text example"]}},
                {"res": {"rec_texts": ["Page two"]}},
            ]
        return [{"res": {"rec_texts": ["An image title", "An image description"]}}]


def test_paddle_v3_image(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakeOCRv3))
    image_path = tmp_path / "example.png"
    image_path.write_bytes(b"fake image")
    result, title = Extractor(mode="paddle_ocr").extract(image_path)
    assert title is None
    assert "An image title" in result
    assert "An image description" in result
    assert "## Page" not in result


def test_paddle_v3_pdf_pages(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakeOCRv3))
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"fake pdf")
    result, _ = Extractor(mode="paddle_ocr").extract(pdf_path)
    assert "## Page 1" in result
    assert "## Page 2" in result
    assert result.index("Page one") < result.index("Page two")


class FakeResult:
    @property
    def json(self):
        return {"res": {"rec_texts": ["Object wrapped output"]}}


def test_paddle_v3_result_json_object():
    result = Extractor._paddle_result_payload(FakeResult())
    assert result["rec_texts"] == ["Object wrapped output"]


class FakeOCRv2:
    def __init__(self, **kwargs):
        self.options = kwargs

    def ocr(self, path, cls=True):
        return [[
            [[0, 0], ("Legacy OCR line", 0.9)],
            [[1, 1], ("Second line", 0.8)],
        ]]


def test_paddle_v2_image(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakeOCRv2))
    image_path = tmp_path / "legacy.jpg"
    image_path.write_bytes(b"fake image")
    result, _ = Extractor(mode="paddle_ocr").extract(image_path)
    assert "Legacy OCR line" in result
    assert "Second line" in result


def test_paddle_v2_pdf_requires_v3(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakeOCRv2))
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"fake pdf")
    with pytest.raises(RuntimeError, match="PaddleOCR 3.x"):
        Extractor(mode="paddle_ocr").extract(pdf_path)
