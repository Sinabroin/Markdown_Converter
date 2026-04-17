"""validator.py 단위 테스트."""

import pytest

from f2md.validator import ValidationResult, _count_headings, _has_repetition, validate


class TestValidationResult:
    def test_to_dict_has_required_fields(self):
        result = ValidationResult(
            passed=True,
            char_count=100,
            heading_count=2,
            repetition_flag=False,
            extraction_ratio=0.5,
        )
        d = result.to_dict()
        required_keys = {
            "passed", "char_count", "heading_count",
            "repetition_flag", "extraction_ratio",
            "failure_reasons", "warnings",
        }
        assert required_keys.issubset(d.keys())


class TestCountHeadings:
    def test_counts_headings(self):
        text = "# H1\n## H2\n### H3\ncontent"
        assert _count_headings(text) == 3

    def test_no_headings(self):
        assert _count_headings("plain text") == 0

    def test_empty_heading_not_counted(self):
        # 빈 헤딩(내용 없음)은 카운트 안 됨
        text = "# \n## \n# Real Title"
        count = _count_headings(text)
        assert count == 1


class TestHasRepetition:
    def test_no_repetition(self):
        text = "normal text without repetition"
        assert not _has_repetition(text, min_length=10, max_count=5)

    def test_repeated_lines(self):
        line = "this is a repeated line"
        text = "\n".join([line] * 6)
        assert _has_repetition(text, min_length=10, max_count=5)

    def test_repeated_lines_below_threshold(self):
        line = "this is a repeated line"
        text = "\n".join([line] * 3)
        assert not _has_repetition(text, min_length=10, max_count=5)

    def test_short_repeated_text_not_flagged(self):
        text = "ab ab ab ab ab ab"
        assert not _has_repetition(text, min_length=10, max_count=5)


class TestValidate:
    def test_empty_string_fails_immediately(self):
        result = validate("")
        assert not result.passed
        assert result.char_count == 0
        assert any("empty" in r for r in result.failure_reasons)

    def test_sufficient_content_passes(self):
        text = "# Title\n\n" + "This is a long enough paragraph. " * 5
        result = validate(text)
        assert result.passed
        assert result.char_count >= 50

    def test_too_short_fails(self):
        text = "Short"
        cfg = {"validation": {"min_char_count": 50, "max_repetition_count": 5,
                              "repetition_min_length": 10, "min_extraction_ratio": 0.01}}
        result = validate(text, cfg=cfg)
        assert not result.passed
        assert any("char_count" in r for r in result.failure_reasons)

    def test_low_extraction_ratio_fails(self):
        text = "# Title\n\nSome content here that is long enough." * 3
        cfg = {"validation": {"min_char_count": 50, "max_repetition_count": 5,
                              "repetition_min_length": 10, "min_extraction_ratio": 0.01}}
        huge_input_size = len(text.encode()) * 10000
        result = validate(text, input_size_bytes=huge_input_size, cfg=cfg)
        assert not result.passed
        assert any("extraction_ratio" in r for r in result.failure_reasons)

    def test_good_extraction_ratio_passes(self):
        text = "# Title\n\n" + "Good content. " * 20
        input_size = len(text.encode())
        result = validate(text, input_size_bytes=input_size)
        assert result.extraction_ratio is not None
        assert result.extraction_ratio >= 0.01

    def test_no_headings_is_warning_not_failure(self):
        text = "Just a plain paragraph. " * 5
        result = validate(text)
        assert result.heading_count == 0
        # 헤딩 없음은 경고만, 실패 사유가 아님
        assert not any("heading" in r for r in result.failure_reasons)
        assert any("heading" in w for w in result.warnings)

    def test_none_input_size_skips_ratio_check(self):
        text = "# Title\n\n" + "content " * 20
        result = validate(text, input_size_bytes=None)
        assert result.extraction_ratio is None
        assert result.passed

    def test_char_count_and_heading_count_returned(self):
        text = "# H1\n## H2\n\n" + "text " * 20
        result = validate(text)
        assert result.char_count == len(text)
        assert result.heading_count == 2

    def test_cfg_min_char_override(self):
        text = "Short text."
        cfg = {"validation": {"min_char_count": 5, "max_repetition_count": 5,
                              "repetition_min_length": 10, "min_extraction_ratio": 0.01}}
        result = validate(text, cfg=cfg)
        assert result.passed

    def test_repetition_flag_triggers_failure(self):
        line = "this is a very repeated line indeed"
        text = "\n".join([line] * 6)
        cfg = {"validation": {"min_char_count": 50, "max_repetition_count": 5,
                              "repetition_min_length": 10, "min_extraction_ratio": 0.01}}
        result = validate(text, cfg=cfg)
        assert result.repetition_flag
        assert not result.passed
