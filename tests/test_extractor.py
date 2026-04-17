"""extractor.py 통합 smoke 테스트 — markitdown 설치 필요."""

import pytest

pytestmark = pytest.mark.skipif(
    condition=False,
    reason="markitdown가 설치되지 않은 경우 스킵",
)


def _markitdown_available() -> bool:
    try:
        import markitdown  # noqa: F401
        return True
    except ImportError:
        return False


requires_markitdown = pytest.mark.skipif(
    not _markitdown_available(),
    reason="markitdown 미설치 — pip install markitdown[all]",
)


@requires_markitdown
class TestExtractorStandardMode:
    """Standard 모드 실제 변환 smoke test."""

    def test_extract_txt_file(self, tmp_path):
        """텍스트 파일을 Markdown으로 변환해야 한다."""
        from f2md.extractor import Extractor

        txt = tmp_path / "test.txt"
        txt.write_text("# Hello\n\nThis is a test document.\n", encoding="utf-8")

        ext = Extractor(mode="standard")
        text, title = ext.extract(txt)

        assert isinstance(text, str)
        assert len(text) > 0

    def test_extract_html_file(self, tmp_path):
        """HTML 파일을 Markdown으로 변환해야 한다."""
        from f2md.extractor import Extractor

        html = tmp_path / "test.html"
        html.write_text(
            "<html><body><h1>Test</h1><p>Hello world</p></body></html>",
            encoding="utf-8",
        )

        ext = Extractor(mode="standard")
        text, title = ext.extract(html)

        assert isinstance(text, str)
        assert len(text) > 0
        assert "Test" in text or "Hello" in text

    def test_extract_csv_file(self, tmp_path):
        """CSV 파일을 Markdown으로 변환해야 한다."""
        from f2md.extractor import Extractor

        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")

        ext = Extractor(mode="standard")
        text, title = ext.extract(csv_file)

        assert isinstance(text, str)
        assert len(text) > 0

    def test_returns_tuple(self, tmp_path):
        """extract()는 (str, str|None) 튜플을 반환해야 한다."""
        from f2md.extractor import Extractor

        txt = tmp_path / "test.txt"
        txt.write_text("Some content here.", encoding="utf-8")

        ext = Extractor(mode="standard")
        result = ext.extract(txt)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)


class TestExtractorInit:
    """Extractor 초기화 테스트 (markitdown 없어도 실행)."""

    @requires_markitdown
    def test_standard_mode_creates_instance(self):
        from f2md.extractor import Extractor

        ext = Extractor(mode="standard")
        assert ext.mode == "standard"
        assert ext._md is not None

    @requires_markitdown
    def test_unknown_mode_falls_back_to_standard(self):
        from f2md.extractor import Extractor

        # 알 수 없는 모드는 else 분기로 standard처럼 동작
        ext = Extractor(mode="unknown_mode")
        assert ext._md is not None
