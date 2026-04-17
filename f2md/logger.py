"""변환 결과 JSON 로그 생성."""

import json
import sys
from datetime import datetime
from pathlib import Path


def write_log(log_dir: Path, log_data: dict) -> Path:
    """변환 결과를 JSON 로그 파일로 저장한다.

    파일 이름: {input_file_stem}.json
    동일 이름 파일이 있으면 덮어쓴다.

    Args:
        log_dir: 로그를 저장할 디렉토리.
        log_data: 로그 딕셔너리. 'input_file' 키 필수.

    Returns:
        생성된 로그 파일 경로.
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    log_data = dict(log_data)
    log_data["timestamp"] = datetime.now().astimezone().isoformat()
    log_data["python_version"] = sys.version.split()[0]

    stem = Path(log_data.get("input_file", "unknown")).stem
    log_path = log_dir / f"{stem}.json"
    log_path.write_text(
        json.dumps(log_data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return log_path


def build_log(
    *,
    input_file: str,
    input_size_bytes: int,
    detected_type: str,
    selected_mode: str,
    escalated_to: str | None,
    retry_count: int,
    markitdown_version: str,
    output_raw: str | None,
    output_clean: str | None,
    validation: dict,
    duration_seconds: float,
    status: str,
    error: str | None = None,
) -> dict:
    """로그 딕셔너리를 표준 형식으로 생성한다.

    모든 필드를 명시적으로 받아 누락 방지.
    """
    return {
        "input_file": input_file,
        "input_size_bytes": input_size_bytes,
        "detected_type": detected_type,
        "selected_mode": selected_mode,
        "escalated_to": escalated_to,
        "retry_count": retry_count,
        "markitdown_version": markitdown_version,
        "output_raw": output_raw,
        "output_clean": output_clean,
        "validation": validation,
        "duration_seconds": round(duration_seconds, 3),
        "status": status,
        "error": error,
    }


def get_markitdown_version() -> str:
    """설치된 markitdown 버전을 반환한다."""
    try:
        from importlib.metadata import version

        return version("markitdown")
    except Exception:
        return "unknown"
