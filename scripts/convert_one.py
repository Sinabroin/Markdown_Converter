"""단일 파일 변환 — 전체 파이프라인 실행.

사용법:
    python scripts\\convert_one.py input\\report.pdf
    python scripts\\convert_one.py input\\report.pdf --force
    python scripts\\convert_one.py input\\report.pdf --mode ocr
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from f2md import config_loader, escalator, extractor, logger, normalizer, router, validator


def convert_one(
    input_path: Path,
    cfg: dict,
    force: bool = False,
    initial_mode: str | None = None,
) -> dict:
    """단일 파일에 대해 전체 변환 파이프라인을 실행한다.

    파이프라인:
    1. 입력 파일 확인
    2. 라우터로 초기 모드 결정
    3. MarkItDown 추출 → raw_md/ 저장
    4. 정규화 → clean_md/ 저장
    5. 검증 → 통과 시 로그, 실패 시 에스컬레이션 또는 failed/

    Args:
        input_path: 변환할 파일 경로.
        cfg: settings.yaml 설정 딕셔너리.
        force: True이면 raw_md/가 이미 있어도 덮어쓴다.
        initial_mode: 강제 지정 모드. None이면 라우터가 결정.

    Returns:
        변환 결과 로그 딕셔너리.
    """
    start_time = time.monotonic()

    paths = cfg["paths"]
    raw_md_dir: Path = paths["raw_md"]
    clean_md_dir: Path = paths["clean_md"]
    json_logs_dir: Path = paths["json_logs"]
    failed_dir: Path = paths["failed"]

    for d in (raw_md_dir, clean_md_dir, json_logs_dir, failed_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1. 입력 파일 확인
    if not input_path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)
    if not input_path.is_file():
        print(f"[ERROR] 경로가 파일이 아닙니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    input_size = input_path.stat().st_size
    markitdown_ver = logger.get_markitdown_version()

    # 2. 모드 결정
    mode = initial_mode or router.route(input_path, cfg)
    if mode == "unknown":
        reason = f"unsupported file type: {input_path.suffix}"
        _move_to_failed(input_path, failed_dir, [reason])
        log_data = logger.build_log(
            input_file=str(input_path),
            input_size_bytes=input_size,
            detected_type=input_path.suffix.lower(),
            selected_mode="unknown",
            escalated_to=None,
            retry_count=0,
            markitdown_version=markitdown_ver,
            output_raw=None,
            output_clean=None,
            validation={},
            duration_seconds=time.monotonic() - start_time,
            status="failed",
            error=reason,
        )
        logger.write_log(json_logs_dir, log_data)
        print(f"[FAILED] {input_path.name}: {reason}")
        return log_data

    # raw_md/ 중복 체크
    raw_path = raw_md_dir / f"{input_path.stem}.md"
    if raw_path.exists() and not force:
        print(f"[SKIP] 이미 변환된 파일입니다: {raw_path.name}  (--force로 재변환)")
        log_data = logger.build_log(
            input_file=str(input_path),
            input_size_bytes=input_size,
            detected_type=input_path.suffix.lower(),
            selected_mode=mode,
            escalated_to=None,
            retry_count=0,
            markitdown_version=markitdown_ver,
            output_raw=str(raw_path),
            output_clean=str(clean_md_dir / f"{input_path.stem}.md"),
            validation={},
            duration_seconds=time.monotonic() - start_time,
            status="skipped",
        )
        logger.write_log(json_logs_dir, log_data)
        return log_data

    # 3~5. 에스컬레이션 루프
    mode_chain = escalator.get_chain(cfg)
    current_mode = mode
    retry_count = 0
    escalated_to: str | None = None
    last_validation: validator.ValidationResult | None = None
    last_error: str | None = None

    while current_mode is not None:
        try:
            # 단계 3: 추출
            ext_instance = extractor.Extractor(mode=current_mode, cfg=cfg)
            raw_text, _ = ext_instance.extract(input_path)

            # raw_md/ 저장 (첫 시도 또는 force 시에만)
            if not raw_path.exists() or force or retry_count > 0:
                raw_path.write_text(raw_text, encoding="utf-8")

            # 단계 4: 정규화
            clean_text = normalizer.normalize(raw_text, cfg)
            clean_path = clean_md_dir / f"{input_path.stem}.md"
            clean_path.write_text(clean_text, encoding="utf-8")

            # 단계 5: 검증
            result = validator.validate(clean_text, input_size, cfg)
            last_validation = result

            if result.passed:
                # 성공
                duration = time.monotonic() - start_time
                log_data = logger.build_log(
                    input_file=str(input_path),
                    input_size_bytes=input_size,
                    detected_type=input_path.suffix.lower(),
                    selected_mode=mode,
                    escalated_to=escalated_to,
                    retry_count=retry_count,
                    markitdown_version=markitdown_ver,
                    output_raw=str(raw_path),
                    output_clean=str(clean_path),
                    validation=result.to_dict(),
                    duration_seconds=duration,
                    status="success",
                )
                if result.warnings:
                    for w in result.warnings:
                        print(f"  [WARN] {w}")
                logger.write_log(json_logs_dir, log_data)
                print(f"[OK] {input_path.name} → {clean_path.name}  ({duration:.2f}s, {current_mode})")
                return log_data
            else:
                # 검증 실패 → 에스컬레이션
                reasons_str = "; ".join(result.failure_reasons)
                print(f"  [ESCALATE] {current_mode} 검증 실패: {reasons_str}")

        except Exception as e:
            last_error = str(e)
            print(f"  [ERROR] {current_mode} 변환 오류: {e}", file=sys.stderr)

        # 다음 모드로
        next_m = escalator.next_mode(current_mode, mode_chain)
        if next_m:
            escalated_to = next_m
            retry_count += 1
        current_mode = next_m

    # 모든 모드 소진 → failed/
    failure_reasons = last_validation.failure_reasons if last_validation else []
    if last_error:
        failure_reasons = [last_error] + failure_reasons

    _move_to_failed(input_path, failed_dir, failure_reasons)
    duration = time.monotonic() - start_time
    log_data = logger.build_log(
        input_file=str(input_path),
        input_size_bytes=input_size,
        detected_type=input_path.suffix.lower(),
        selected_mode=mode,
        escalated_to=escalated_to,
        retry_count=retry_count,
        markitdown_version=markitdown_ver,
        output_raw=str(raw_path) if raw_path.exists() else None,
        output_clean=None,
        validation=last_validation.to_dict() if last_validation else {},
        duration_seconds=duration,
        status="failed",
        error="; ".join(failure_reasons),
    )
    logger.write_log(json_logs_dir, log_data)
    print(f"[FAILED] {input_path.name}: 모든 모드 소진 → failed/")
    return log_data


def _move_to_failed(input_path: Path, failed_dir: Path, reasons: list[str]) -> None:
    """파일을 failed/ 디렉토리로 복사하고 사유 JSON을 저장한다."""
    import json
    from datetime import datetime

    failed_dir.mkdir(parents=True, exist_ok=True)
    dest = failed_dir / input_path.name
    shutil.copy2(str(input_path), str(dest))

    reason_json = {
        "input_file": input_path.name,
        "failure_reasons": reasons,
        "timestamp": datetime.now().astimezone().isoformat(),
    }
    reason_path = failed_dir / f"{input_path.stem}_failure.json"
    reason_path.write_text(
        json.dumps(reason_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="파일을 Markdown으로 변환합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="변환할 파일 경로")
    parser.add_argument(
        "--force",
        action="store_true",
        help="raw_md/에 이미 파일이 있어도 재변환합니다.",
    )
    parser.add_argument(
        "--mode",
        choices=["standard", "ocr", "high_accuracy"],
        default=None,
        help="변환 모드를 강제 지정합니다 (기본: 자동 라우팅).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="설정 파일 경로 (기본: config/settings.yaml).",
    )

    args = parser.parse_args()

    root = ROOT if args.config is None else args.config.parent.parent
    cfg = config_loader.load_config(root)

    result = convert_one(
        input_path=args.input.resolve(),
        cfg=cfg,
        force=args.force,
        initial_mode=args.mode,
    )

    sys.exit(0 if result.get("status") in ("success", "skipped") else 1)


if __name__ == "__main__":
    main()
