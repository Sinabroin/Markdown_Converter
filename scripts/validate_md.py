"""Markdown 검증 단독 실행.

사용법:
    python scripts\\validate_md.py output\\clean_md\\report.md
    python scripts\\validate_md.py output\\clean_md\\report.md --input-size 204800
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from f2md import config_loader, validator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="정규화된 Markdown 파일의 품질을 검증합니다.",
    )
    parser.add_argument("input", type=Path, help="검증할 .md 파일 경로")
    parser.add_argument(
        "--input-size",
        type=int,
        default=None,
        help="원본 파일 크기 (바이트). 추출 비율 검증에 사용.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="결과를 JSON 형식으로 출력합니다.",
    )

    args = parser.parse_args()
    input_path: Path = args.input.resolve()

    if not input_path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    clean_text = input_path.read_text(encoding="utf-8")
    cfg = config_loader.load_config(ROOT)
    result = validator.validate(clean_text, args.input_size, cfg)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {input_path.name}")
        print(f"  문자 수      : {result.char_count}")
        print(f"  헤딩 수      : {result.heading_count}")
        print(f"  반복 이상    : {result.repetition_flag}")
        if result.extraction_ratio is not None:
            print(f"  추출 비율    : {result.extraction_ratio:.4f}")
        if result.failure_reasons:
            print("  실패 사유:")
            for r in result.failure_reasons:
                print(f"    - {r}")
        if result.warnings:
            print("  경고:")
            for w in result.warnings:
                print(f"    - {w}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
