"""Markdown 정규화 단독 실행.

사용법:
    python scripts\\normalize_md.py output\\raw_md\\report.md
    python scripts\\normalize_md.py output\\raw_md\\report.md -o output\\clean_md\\report.md
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from f2md import config_loader, normalizer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Markdown 파일을 정규화합니다.",
    )
    parser.add_argument("input", type=Path, help="정규화할 .md 파일 경로")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="출력 경로 (기본: config의 clean_md/ 디렉토리에 같은 파일명 저장).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="결과를 표준 출력에 출력합니다 (파일 저장 안 함).",
    )

    args = parser.parse_args()
    input_path: Path = args.input.resolve()

    if not input_path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    raw_text = input_path.read_text(encoding="utf-8")

    cfg = config_loader.load_config(ROOT)
    clean_text = normalizer.normalize(raw_text, cfg)

    if args.stdout:
        print(clean_text)
        return

    if args.output:
        out_path = args.output
    else:
        clean_md_dir: Path = cfg["paths"]["clean_md"]
        clean_md_dir.mkdir(parents=True, exist_ok=True)
        out_path = clean_md_dir / input_path.name

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(clean_text, encoding="utf-8")
    print(f"[OK] 정규화 완료: {out_path}")


if __name__ == "__main__":
    main()
