"""디렉토리 배치 변환 — ThreadPoolExecutor + 진행률 + 배치 리포트.

사용법:
    python scripts\\convert_batch.py input\\
    python scripts\\convert_batch.py input\\ --recursive
    python scripts\\convert_batch.py input\\ --recursive --workers 8
    python scripts\\convert_batch.py input\\ --force
"""

import argparse
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from f2md import config_loader, router

# scripts/ 디렉토리를 경로에 추가해 convert_one을 임포트
_SCRIPTS_DIR = Path(__file__).parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from convert_one import convert_one  # noqa: E402

# 지원 확장자 목록 (unknown 제외)
SUPPORTED_EXTENSIONS = set(router.EXTENSION_MAP.keys())

# 진행률 출력을 위한 스레드 락
_print_lock = threading.Lock()


def safe_print(msg: str) -> None:
    """스레드 안전 출력."""
    with _print_lock:
        print(msg, flush=True)


def collect_files(input_dir: Path, recursive: bool) -> list[Path]:
    """입력 디렉토리에서 변환 대상 파일 목록을 수집한다."""
    pattern = "**/*" if recursive else "*"
    files = [
        p for p in input_dir.glob(pattern)
        if p.is_file() and not p.name.startswith(".")
    ]
    return sorted(files)


def run_batch(
    input_dir: Path,
    cfg: dict,
    recursive: bool = False,
    force: bool = False,
    max_workers: int | None = None,
) -> dict:
    """배치 변환을 실행하고 결과 요약을 반환한다.

    Args:
        input_dir: 변환할 파일이 있는 디렉토리.
        cfg: settings.yaml 설정 딕셔너리.
        recursive: True이면 하위 디렉토리 포함.
        force: True이면 기존 raw_md/ 파일 덮어쓰기.
        max_workers: 스레드 풀 워커 수. None이면 settings.yaml 값 사용.

    Returns:
        배치 결과 요약 딕셔너리.
    """
    files = collect_files(input_dir, recursive)
    if not files:
        print(f"[INFO] 변환할 파일이 없습니다: {input_dir}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0, "details": []}

    total = len(files)
    workers = max_workers or cfg.get("batch", {}).get("max_workers", 4)
    continue_on_error = cfg.get("batch", {}).get("continue_on_error", True)

    results = {"total": total, "success": 0, "failed": 0, "skipped": 0, "details": []}
    counter = {"done": 0}

    def process_file(file_path: Path) -> dict:
        try:
            log = convert_one(file_path, cfg, force=force)
            status = log.get("status", "failed")
            error = log.get("error")
            return {"file": file_path.name, "status": status, "error": error}
        except Exception as e:
            return {"file": file_path.name, "status": "failed", "error": str(e)}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_file = {executor.submit(process_file, f): f for f in files}

        for future in as_completed(future_to_file):
            with _print_lock:
                counter["done"] += 1
                done = counter["done"]

            detail = future.result()
            results["details"].append(detail)

            status = detail["status"]
            if status == "success":
                results["success"] += 1
            elif status == "skipped":
                results["skipped"] += 1
            else:
                results["failed"] += 1
                if not continue_on_error:
                    safe_print(f"\n[ABORT] 오류 발생으로 중단: {detail['file']}")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

            marker = "OK" if status == "success" else ("SKIP" if status == "skipped" else "FAIL")
            safe_print(f"[{done}/{total}] {detail['file']} ... {marker}")

    return results


def print_report(results: dict, log_dir: Path) -> None:
    """배치 완료 요약 리포트를 출력한다."""
    print("\n" + "=" * 40)
    print("=== Batch Complete ===")
    print("=" * 40)
    print(f"Total  : {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Failed : {results['failed']}")

    failed_items = [d for d in results["details"] if d["status"] == "failed"]
    if failed_items:
        print("\nFailed files:")
        for item in failed_items:
            error = f" ({item['error']})" if item.get("error") else ""
            print(f"  - {item['file']}{error}")

    print(f"\nLogs: {log_dir}")
    print("=" * 40)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="디렉토리 내 파일을 일괄 Markdown으로 변환합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_dir", type=Path, help="변환할 파일이 있는 디렉토리")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="하위 디렉토리까지 포함합니다.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="raw_md/에 이미 파일이 있어도 재변환합니다.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="병렬 워커 수 (기본: settings.yaml의 batch.max_workers).",
    )

    args = parser.parse_args()

    input_dir: Path = args.input_dir.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] 디렉토리를 찾을 수 없습니다: {input_dir}", file=sys.stderr)
        sys.exit(1)

    cfg = config_loader.load_config(ROOT)
    results = run_batch(
        input_dir=input_dir,
        cfg=cfg,
        recursive=args.recursive,
        force=args.force,
        max_workers=args.workers,
    )

    print_report(results, cfg["paths"]["json_logs"])
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
