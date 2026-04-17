"""normalizer.py 단위 테스트."""

import pytest

from f2md.normalizer import (
    _collapse_blank_lines,
    _collapse_repeated_tokens,
    _protect_code_blocks,
    _remove_empty_headings,
    _restore_code_blocks,
    _strip_trailing_whitespace,
    _unify_bullets,
    normalize,
)


class TestStripTrailingWhitespace:
    def test_removes_trailing_spaces(self):
        text = "hello   \nworld  \n"
        assert _strip_trailing_whitespace(text) == "hello\nworld\n"

    def test_preserves_non_trailing_spaces(self):
        text = "  indented line  \n"
        assert _strip_trailing_whitespace(text) == "  indented line\n"

    def test_empty_string(self):
        assert _strip_trailing_whitespace("") == ""


class TestCollapseBlankLines:
    def test_collapses_three_newlines_to_two(self):
        text = "para1\n\n\npara2"
        assert _collapse_blank_lines(text) == "para1\n\npara2"

    def test_collapses_many_newlines(self):
        text = "a\n\n\n\n\nb"
        assert _collapse_blank_lines(text) == "a\n\nb"

    def test_preserves_double_newline(self):
        text = "a\n\nb"
        assert _collapse_blank_lines(text) == "a\n\nb"

    def test_custom_max_newlines(self):
        text = "a\n\n\nb"
        # max=1이면 2개 이상의 개행을 1개로
        assert _collapse_blank_lines(text, max_consecutive=1) == "a\nb"


class TestUnifyBullets:
    def test_asterisk_to_dash(self):
        text = "* item1\n* item2"
        assert _unify_bullets(text) == "- item1\n- item2"

    def test_plus_to_dash(self):
        text = "+ item1\n+ item2"
        assert _unify_bullets(text) == "- item1\n- item2"

    def test_existing_dash_unchanged(self):
        text = "- item1\n- item2"
        assert _unify_bullets(text) == "- item1\n- item2"

    def test_indented_bullets(self):
        text = "  * nested"
        assert _unify_bullets(text) == "  - nested"

    def test_non_bullet_asterisk_unchanged(self):
        text = "**bold** text"
        assert _unify_bullets(text) == "**bold** text"

    def test_mixed_bullets(self):
        text = "* a\n+ b\n- c"
        assert _unify_bullets(text) == "- a\n- b\n- c"


class TestRemoveEmptyHeadings:
    def test_removes_heading_with_only_spaces(self):
        text = "## \n# \ncontent"
        result = _remove_empty_headings(text)
        assert "## " not in result.split("\n")
        assert "content" in result

    def test_preserves_headings_with_content(self):
        text = "# Title\n## Section"
        result = _remove_empty_headings(text)
        assert "# Title" in result
        assert "## Section" in result

    def test_removes_heading_with_no_text(self):
        lines = _remove_empty_headings("###\n").split("\n")
        assert "###" not in lines


class TestCollapseRepeatedTokens:
    def test_no_repetition_unchanged(self):
        text = "hello world"
        assert _collapse_repeated_tokens(text) == text

    def test_short_token_unchanged(self):
        text = "ab ab ab ab ab"
        assert _collapse_repeated_tokens(text) == text

    def test_long_token_repeated(self):
        token = "hello world!"
        repeated = (token * 3) + " extra"
        result = _collapse_repeated_tokens(repeated)
        assert result.count(token) < 3


class TestProtectAndRestoreCodeBlocks:
    def test_fenced_block_preserved(self):
        text = "before\n```python\ncode here\n```\nafter"
        protected, blocks = _protect_code_blocks(text)
        assert "code here" not in protected
        restored = _restore_code_blocks(protected, blocks)
        assert restored == text

    def test_multiple_blocks(self):
        text = "```\nblock1\n```\nmiddle\n```\nblock2\n```"
        protected, blocks = _protect_code_blocks(text)
        assert len(blocks) == 2
        restored = _restore_code_blocks(protected, blocks)
        assert restored == text


class TestNormalize:
    def test_empty_string(self):
        assert normalize("") == ""

    def test_basic_normalization(self):
        text = "# Title   \n\n\n\nParagraph.\n"
        result = normalize(text)
        assert "   " not in result
        assert "\n\n\n" not in result

    def test_code_block_content_preserved(self):
        code = "```python\n* not a bullet\n## not a heading\n```"
        result = normalize(code)
        assert "* not a bullet" in result
        assert "## not a heading" in result

    def test_bullets_unified(self):
        text = "* item1\n+ item2\n- item3"
        result = normalize(text)
        assert result == "- item1\n- item2\n- item3"

    def test_trailing_whitespace_removed(self):
        text = "line with spaces   \nanother line  "
        result = normalize(text)
        for line in result.split("\n"):
            assert line == line.rstrip()

    def test_empty_headings_removed(self):
        text = "## \n# Title\n## \ncontent"
        result = normalize(text)
        lines = result.split("\n")
        empty_headings = [l for l in lines if l.strip() in ("##", "##  ", "#")]
        # 내용 없는 헤딩은 제거되어야 함
        for l in lines:
            import re
            assert not re.match(r"^#{1,6}\s*$", l), f"빈 헤딩이 남아 있음: {repr(l)}"

    def test_leading_trailing_blank_lines_stripped(self):
        text = "\n\n# Title\n\ncontent\n\n"
        result = normalize(text)
        assert not result.startswith("\n")
        assert not result.endswith("\n")

    def test_cfg_overrides_bullet_char(self):
        text = "* item"
        cfg = {"normalization": {"bullet_char": "*", "max_consecutive_newlines": 2}}
        result = normalize(text, cfg)
        assert result == "* item"
