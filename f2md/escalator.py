"""모드 에스컬레이션 관리."""

DEFAULT_MODE_CHAIN = ["standard", "paddle_ocr", "ocr", "high_accuracy"]


def next_mode(current: str, chain: list[str] | None = None) -> str | None:
    """현재 모드의 다음 에스컬레이션 모드를 반환한다.

    Args:
        current: 현재 변환 모드.
        chain: 에스컬레이션 순서 목록. None이면 기본 체인 사용.

    Returns:
        다음 모드 문자열, 더 이상 없으면 None.

    Example:
        >>> next_mode("standard")
        'paddle_ocr'
        >>> next_mode("paddle_ocr")
        'ocr'
        >>> next_mode("high_accuracy")
        None
    """
    chain = chain or DEFAULT_MODE_CHAIN
    try:
        idx = chain.index(current)
        return chain[idx + 1] if idx + 1 < len(chain) else None
    except ValueError:
        return None


def get_chain(cfg: dict | None = None) -> list[str]:
    """설정에서 에스컬레이션 체인을 반환한다."""
    if cfg:
        return cfg.get("modes", {}).get("chain", DEFAULT_MODE_CHAIN)
    return DEFAULT_MODE_CHAIN
