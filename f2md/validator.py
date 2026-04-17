"""Markdown 품질 검증 — ValidationResult dataclass + 5개 검증 항목."""

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """변환 품질 검증 결과."""

    passed: bool
    char_count: int
    heading_count: int
    repetition_flag: bool
    extraction_ratio: float | None
    failure_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """로그용 딕셔너리로 변환한다."""
        return {
            "passed": self.passed,
            "char_count": self.char_count,
            "heading_count": self.heading_count,
            "repetition_flag": self.repetition_flag,
            "extraction_ratio": self.extraction_ratio,
            "failure_reasons": self.failure_reasons,
            "warnings": self.warnings,
        }


def validate(
    clean_md: str,
    input_size_bytes: int | None = None,
    cfg: dict | None = None,
) -> ValidationResult:
    """정규화된 Markdown을 검증한다.

    검증 항목:
    1. 비어 있지 않음: len > 0 → 즉시 실패
    2. 최소 길이: char_count >= min_char_count → 에스컬레이션
    3. 헤딩 보존: # 1개+ → 경고 로그만 (에스컬레이션 안 함)
    4. 반복 이상: 10자+ 5회+ 반복 → 에스컬레이션
    5. 추출 비율: len/input_size >= 0.01 → 에스컬레이션

    Args:
        clean_md: 검증할 정규화된 Markdown 문자열.
        input_size_bytes: 원본 파일 크기 (바이트). None이면 추출 비율 검증 생략.
        cfg: settings.yaml 설정 딕셔너리 (validation 섹션 사용).

    Returns:
        ValidationResult 인스턴스.
    """
    cfg = cfg or {}
    v_cfg = cfg.get("validation", {})
    min_char = v_cfg.get("min_char_count", 50)
    max_rep_count = v_cfg.get("max_repetition_count", 5)
    rep_min_len = v_cfg.get("repetition_min_length", 10)
    min_ratio = v_cfg.get("min_extraction_ratio", 0.01)

    failure_reasons: list[str] = []
    warnings: list[str] = []

    char_count = len(clean_md)
    heading_count = _count_headings(clean_md)
    repetition_flag = _has_repetition(clean_md, rep_min_len, max_rep_count)
    extraction_ratio = (
        char_count / input_size_bytes if input_size_bytes and input_size_bytes > 0 else None
    )

    # 검증 1: 비어 있지 않음 (즉시 실패 — 에스컬레이션 불필요)
    if char_count == 0:
        failure_reasons.append("empty output: char_count=0")
        return ValidationResult(
            passed=False,
            char_count=0,
            heading_count=0,
            repetition_flag=False,
            extraction_ratio=extraction_ratio,
            failure_reasons=failure_reasons,
            warnings=warnings,
        )

    # 검증 2: 최소 길이
    if char_count < min_char:
        failure_reasons.append(f"char_count={char_count} < min={min_char}")

    # 검증 3: 헤딩 보존 (경고만)
    if heading_count == 0:
        warnings.append("no headings found in output")

    # 검증 4: 반복 이상
    if repetition_flag:
        failure_reasons.append(
            f"repetition detected: same {rep_min_len}+ char string repeated {max_rep_count}+ times"
        )

    # 검증 5: 추출 비율
    if extraction_ratio is not None and extraction_ratio < min_ratio:
        failure_reasons.append(
            f"extraction_ratio={extraction_ratio:.4f} < min={min_ratio}"
        )

    passed = len(failure_reasons) == 0
    return ValidationResult(
        passed=passed,
        char_count=char_count,
        heading_count=heading_count,
        repetition_flag=repetition_flag,
        extraction_ratio=extraction_ratio,
        failure_reasons=failure_reasons,
        warnings=warnings,
    )


def _count_headings(text: str) -> int:
    """Markdown 헤딩(# ~ ######)의 수를 반환한다."""
    return len(re.findall(r"^#{1,6}\s+\S", text, re.MULTILINE))


def _has_repetition(text: str, min_length: int, max_count: int) -> bool:
    """min_length자 이상 동일 문자열이 max_count회 이상 반복되는지 검사한다.

    줄 단위로 검사하며, 연속 줄의 반복과 단일 줄 내 반복 모두 감지한다.
    """
    # 줄 단위 반복 감지 (연속된 동일 줄)
    lines = [l for l in text.split("\n") if l.strip()]
    if _check_line_repetition(lines, min_length, max_count):
        return True

    # 단일 줄 내 부분 문자열 반복 감지
    for line in lines:
        if len(line) >= min_length * max_count:
            if _check_substring_repetition(line, min_length, max_count):
                return True

    return False


def _check_line_repetition(lines: list[str], min_length: int, max_count: int) -> bool:
    """연속된 동일 줄이 max_count회 이상 반복되는지 확인한다."""
    if not lines:
        return False

    consecutive = 1
    for i in range(1, len(lines)):
        if lines[i] == lines[i - 1] and len(lines[i]) >= min_length:
            consecutive += 1
            if consecutive >= max_count:
                return True
        else:
            consecutive = 1
    return False


def _check_substring_repetition(line: str, min_length: int, max_count: int) -> bool:
    """단일 줄 안에서 부분 문자열이 max_count회 이상 반복되는지 확인한다."""
    for token_len in range(min_length, len(line) // max_count + 1):
        for start in range(len(line) - token_len * max_count + 1):
            token = line[start:start + token_len]
            if token * max_count in line:
                return True
    return False
