"""파일 확장자 / MIME 기반 변환 모드 라우팅."""

from pathlib import Path

EXTENSION_MAP: dict[str, str] = {
    ".pdf": "standard",
    ".docx": "standard",
    ".doc": "standard",
    ".pptx": "standard",
    ".ppt": "standard",
    ".xlsx": "standard",
    ".xls": "standard",
    ".csv": "standard",
    ".html": "standard",
    ".htm": "standard",
    ".json": "standard",
    ".xml": "standard",
    ".epub": "standard",
    ".zip": "standard",
    ".txt": "standard",
    ".md": "standard",
    ".rst": "standard",
    ".jpg": "standard",
    ".jpeg": "standard",
    ".png": "standard",
    ".gif": "standard",
    ".webp": "standard",
    ".bmp": "standard",
}

# MIME 타입 → 모드 매핑 (magika 결과 기반)
MIME_MAP: dict[str, str] = {
    "application/pdf": "standard",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "standard",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "standard",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "standard",
    "text/html": "standard",
    "text/csv": "standard",
    "text/plain": "standard",
    "application/json": "standard",
    "application/xml": "standard",
    "text/xml": "standard",
    "application/epub+zip": "standard",
    "application/zip": "standard",
    "image/jpeg": "standard",
    "image/png": "standard",
    "image/gif": "standard",
    "image/webp": "standard",
    "image/bmp": "standard",
    "image/tiff": "ocr",
}


def route(file_path: Path, cfg: dict | None = None) -> str:
    """파일 경로를 분석해 변환 모드를 결정한다.

    우선순위:
    1. cfg의 extension_overrides (사용자 재정의)
    2. EXTENSION_MAP (확장자 기반)
    3. magika MIME 감지 (확장자 불명 시)
    4. 'unknown' (판별 불가)

    Args:
        file_path: 변환할 파일 경로.
        cfg: settings.yaml 설정 딕셔너리. None이면 기본값 사용.

    Returns:
        모드 문자열: 'standard', 'ocr', 'high_accuracy', 'unknown'
    """
    ext = file_path.suffix.lower()

    # 1. 사용자 재정의 확장자 오버라이드
    if cfg:
        overrides = cfg.get("modes", {}).get("extension_overrides", {})
        if ext in overrides:
            return overrides[ext]

    # 2. 확장자 기반 1차 판별
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]

    # 3. MIME 기반 2차 판별 (magika)
    mime_mode = _detect_via_mime(file_path)
    if mime_mode:
        return mime_mode

    return "unknown"


def _detect_via_mime(file_path: Path) -> str | None:
    """magika로 MIME 타입을 감지하고 모드를 반환한다.

    Returns:
        감지된 모드 문자열, 판별 불가 시 None.
    """
    try:
        from magika import Magika

        m = Magika()
        result = m.identify_path(file_path)
        mime_type = result.output.mime_type
        return MIME_MAP.get(mime_type)
    except ImportError:
        return None
    except Exception:
        return None
