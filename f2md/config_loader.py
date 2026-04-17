"""settings.yaml 파싱 및 경로 절대화."""

from pathlib import Path

import yaml


def load_config(root: Path | None = None) -> dict:
    """settings.yaml을 로드하고 경로를 절대 경로로 변환한다.

    Args:
        root: 프로젝트 루트 경로. None이면 이 파일 기준 상위 2단계 사용.

    Returns:
        설정 딕셔너리. paths 섹션의 값은 절대 Path 객체.
    """
    if root is None:
        root = Path(__file__).parent.parent

    config_path = root / "config" / "settings.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # paths 섹션의 상대 경로를 절대 경로로 변환
    if "paths" in cfg:
        cfg["paths"] = {
            key: (root / value).resolve()
            for key, value in cfg["paths"].items()
        }

    cfg["_root"] = root.resolve()
    return cfg


def get_path(cfg: dict, key: str) -> Path:
    """설정에서 경로 값을 꺼내 Path 객체로 반환한다."""
    return cfg["paths"][key]
