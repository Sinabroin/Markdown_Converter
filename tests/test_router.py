"""router.py 단위 테스트."""

from pathlib import Path

import pytest

from f2md.router import EXTENSION_MAP, route


class TestRouteByExtension:
    """확장자 기반 라우팅 테스트."""

    @pytest.mark.parametrize("ext,expected_mode", [
        (".pdf", "standard"),
        (".docx", "standard"),
        (".pptx", "standard"),
        (".xlsx", "standard"),
        (".csv", "standard"),
        (".html", "standard"),
        (".htm", "standard"),
        (".json", "standard"),
        (".xml", "standard"),
        (".epub", "standard"),
        (".zip", "standard"),
        (".txt", "standard"),
        (".md", "standard"),
        (".jpg", "standard"),
        (".jpeg", "standard"),
        (".png", "standard"),
    ])
    def test_known_extensions_return_standard(self, ext, expected_mode, tmp_path):
        """알려진 확장자는 standard 모드를 반환해야 한다."""
        f = tmp_path / f"test{ext}"
        f.touch()
        assert route(f) == expected_mode

    def test_unknown_extension_returns_unknown(self, tmp_path):
        """알 수 없는 확장자는 unknown을 반환해야 한다."""
        f = tmp_path / "test.xyz"
        f.touch()
        result = route(f)
        assert result == "unknown"

    def test_case_insensitive_extension(self, tmp_path):
        """확장자 대소문자를 구분하지 않아야 한다."""
        f = tmp_path / "test.PDF"
        f.touch()
        assert route(f) == "standard"

    def test_extension_override_in_cfg(self, tmp_path):
        """cfg의 extension_overrides가 기본 매핑보다 우선해야 한다."""
        f = tmp_path / "test.tif"
        f.touch()
        cfg = {"modes": {"extension_overrides": {".tif": "ocr"}}}
        assert route(f, cfg) == "ocr"

    def test_override_does_not_affect_other_extensions(self, tmp_path):
        """extension_overrides는 지정된 확장자만 영향을 줘야 한다."""
        f = tmp_path / "test.pdf"
        f.touch()
        cfg = {"modes": {"extension_overrides": {".tif": "ocr"}}}
        assert route(f, cfg) == "standard"

    def test_no_extension_returns_unknown(self, tmp_path):
        """확장자가 없는 파일은 unknown을 반환해야 한다."""
        f = tmp_path / "noextension"
        f.touch()
        result = route(f)
        assert result in ("unknown",)

    def test_extension_map_completeness(self):
        """EXTENSION_MAP에 Phase 1 필수 포맷이 모두 포함되어야 한다."""
        required = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".csv",
                    ".json", ".xml", ".epub", ".zip", ".jpg", ".png", ".txt"}
        for ext in required:
            assert ext in EXTENSION_MAP, f"필수 확장자 누락: {ext}"
