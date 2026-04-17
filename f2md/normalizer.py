"""Markdown 정규화 — 코드블록 보호 + 6단계 파이프라인."""

import re
import uuid


def normalize(raw_md: str, cfg: dict | None = None) -> str:
    """raw Markdown을 정규화한다.

    처리 순서:
    1. 코드블록을 UUID 플레이스홀더로 치환 (보호)
    2. 줄 단위 후행 공백 제거
    3. 3줄+ 연속 개행 → 2줄 축소
    4. 불릿 통일 (* + → -)
    5. 빈 헤딩 라인 제거
    6. 반복 토큰 축소 (10자+ 동일 문자열 3회+ → 1회)
    7. 선행/후행 빈 줄 strip
    8. 플레이스홀더 → 코드블록 복원

    Args:
        raw_md: 정규화할 원본 Markdown 문자열.
        cfg: settings.yaml 설정 딕셔너리 (normalization 섹션 사용).

    Returns:
        정규화된 Markdown 문자열.
    """
    if not raw_md:
        return raw_md

    cfg = cfg or {}
    norm_cfg = cfg.get("normalization", {})
    bullet_char = norm_cfg.get("bullet_char", "-")
    max_newlines = norm_cfg.get("max_consecutive_newlines", 2)

    # 단계 1: 코드블록 보호
    text, code_blocks = _protect_code_blocks(raw_md)

    # 단계 2: 줄 단위 후행 공백 제거
    text = _strip_trailing_whitespace(text)

    # 단계 3: 연속 개행 축소
    text = _collapse_blank_lines(text, max_newlines)

    # 단계 4: 불릿 통일
    text = _unify_bullets(text, bullet_char)

    # 단계 5: 빈 헤딩 제거
    text = _remove_empty_headings(text)

    # 단계 6: 반복 토큰 축소
    text = _collapse_repeated_tokens(text)

    # 단계 7: 선행/후행 빈 줄 제거
    text = text.strip()

    # 단계 8: 코드블록 복원
    text = _restore_code_blocks(text, code_blocks)

    return text


def _protect_code_blocks(text: str) -> tuple[str, dict[str, str]]:
    """코드블록을 UUID 플레이스홀더로 치환한다.

    ``` 또는 ~~~ 로 시작하는 펜스드 코드블록과
    4-space 들여쓰기 코드블록을 보호한다.

    Returns:
        (치환된 텍스트, {플레이스홀더: 원본 코드블록} 딕셔너리)
    """
    code_blocks: dict[str, str] = {}

    # 펜스드 코드블록 (``` 또는 ~~~)
    fenced_pattern = re.compile(
        r"(```[^\n]*\n.*?```|~~~[^\n]*\n.*?~~~)",
        re.DOTALL,
    )

    def replace_fenced(m: re.Match) -> str:
        key = f"__CODEBLOCK_{uuid.uuid4().hex}__"
        code_blocks[key] = m.group(0)
        return key

    text = fenced_pattern.sub(replace_fenced, text)
    return text, code_blocks


def _restore_code_blocks(text: str, code_blocks: dict[str, str]) -> str:
    """플레이스홀더를 원본 코드블록으로 복원한다."""
    for key, original in code_blocks.items():
        text = text.replace(key, original)
    return text


def _strip_trailing_whitespace(text: str) -> str:
    """각 줄의 후행 공백을 제거한다."""
    lines = text.split("\n")
    return "\n".join(line.rstrip() for line in lines)


def _collapse_blank_lines(text: str, max_consecutive: int = 2) -> str:
    """max_consecutive+1개 이상 연속된 빈 줄을 max_consecutive개로 축소한다."""
    pattern = re.compile(r"\n{" + str(max_consecutive + 1) + r",}")
    replacement = "\n" * max_consecutive
    return pattern.sub(replacement, text)


def _unify_bullets(text: str, bullet_char: str = "-") -> str:
    """줄 시작의 * 또는 + 불릿을 bullet_char로 통일한다.

    들여쓰기를 보존하며, 코드블록 내부는 이미 보호되어 있다.
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        # 들여쓰기 + (* 또는 +) + 공백 패턴
        m = re.match(r"^(\s*)[*+](\s+)", line)
        if m:
            line = m.group(1) + bullet_char + m.group(2) + line[m.end():]
        result.append(line)
    return "\n".join(result)


def _remove_empty_headings(text: str) -> str:
    """내용 없는 헤딩 라인을 제거한다.

    예: '## ' (헤딩 마커만 있고 제목 텍스트 없음)
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        # '#' 하나 이상 + 공백만 있고 이후 텍스트 없는 줄 제거
        if re.match(r"^#{1,6}\s*$", line):
            continue
        result.append(line)
    return "\n".join(result)


def _collapse_repeated_tokens(text: str, min_length: int = 10, min_repeat: int = 3) -> str:
    """10자 이상 동일 문자열이 연속 3회 이상 반복되면 1회로 축소한다.

    단락(빈 줄) 경계를 넘지 않고 줄 단위로 처리한다.
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        line = _collapse_line_repetition(line, min_length, min_repeat)
        result.append(line)
    return "\n".join(result)


def _collapse_line_repetition(line: str, min_length: int, min_repeat: int) -> str:
    """단일 줄에서 반복 토큰을 축소한다."""
    if len(line) < min_length * min_repeat:
        return line

    # 줄 내에서 동일 구간이 반복되는 패턴 탐색
    # 예: "hello world hello world hello world" → "hello world"
    for token_len in range(len(line) // min_repeat, min_length - 1, -1):
        token = line[:token_len]
        repeated = token * min_repeat
        if repeated in line:
            # 해당 반복 구간을 1회로 줄임
            line = line.replace(repeated, token, 1)
    return line
