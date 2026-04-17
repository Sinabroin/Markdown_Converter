"""pytest 공통 픽스처."""

import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 Python 경로에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def cfg(tmp_path):
    """임시 디렉토리를 사용하는 설정 딕셔너리."""
    return {
        "_root": tmp_path,
        "paths": {
            "input": tmp_path / "input",
            "raw_md": tmp_path / "output" / "raw_md",
            "clean_md": tmp_path / "output" / "clean_md",
            "json_logs": tmp_path / "output" / "json_logs",
            "failed": tmp_path / "output" / "failed",
        },
        "modes": {
            "default": "standard",
            "chain": ["standard", "ocr", "high_accuracy"],
            "max_retries": 3,
            "extension_overrides": {".tif": "ocr", ".tiff": "ocr"},
        },
        "validation": {
            "min_char_count": 50,
            "max_repetition_count": 5,
            "repetition_min_length": 10,
            "min_extraction_ratio": 0.01,
        },
        "normalization": {
            "bullet_char": "-",
            "max_consecutive_newlines": 2,
        },
        "batch": {
            "max_workers": 2,
            "continue_on_error": True,
        },
    }


@pytest.fixture
def sample_txt(tmp_path) -> Path:
    """최소 크기의 텍스트 파일 픽스처."""
    p = tmp_path / "sample.txt"
    p.write_text(
        "# Sample Document\n\nThis is a sample text file.\n\n"
        "It has multiple paragraphs for testing.\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def sample_html(tmp_path) -> Path:
    """최소 HTML 파일 픽스처."""
    p = tmp_path / "sample.html"
    p.write_text(
        "<!DOCTYPE html>\n<html>\n<head><title>Test</title></head>\n"
        "<body><h1>Hello World</h1><p>This is a test paragraph.</p></body>\n</html>",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    """최소 CSV 파일 픽스처."""
    p = tmp_path / "sample.csv"
    p.write_text(
        "name,age,city\nAlice,30,Seoul\nBob,25,Busan\nCharlie,35,Incheon\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def unknown_file(tmp_path) -> Path:
    """지원하지 않는 확장자 파일 픽스처."""
    p = tmp_path / "unknown.xyz"
    p.write_text("some content", encoding="utf-8")
    return p
