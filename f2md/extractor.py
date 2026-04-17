"""MarkItDown 래퍼 — standard / ocr / high_accuracy 3-way 모드."""

import os
from pathlib import Path


class Extractor:
    """MarkItDown을 감싸는 변환 엔진.

    모드별 MarkItDown 인스턴스를 생성하고 파일을 Markdown으로 변환한다.
    """

    def __init__(self, mode: str = "standard", cfg: dict | None = None):
        """Extractor를 초기화한다.

        Args:
            mode: 'standard', 'ocr', 'high_accuracy' 중 하나.
            cfg: settings.yaml 설정 딕셔너리. OCR/high_accuracy 모드에 필요.
        """
        from markitdown import MarkItDown

        self.mode = mode
        cfg = cfg or {}

        if mode == "ocr":
            llm_client = self._build_llm_client(cfg)
            llm_model = cfg.get("ocr", {}).get("llm_model", "gpt-4o")
            self._md = MarkItDown(
                enable_plugins=True,
                llm_client=llm_client,
                llm_model=llm_model,
            )
        elif mode == "high_accuracy":
            endpoint = os.environ.get(
                "F2MD_DOCINTEL_ENDPOINT",
                cfg.get("high_accuracy", {}).get("endpoint", ""),
            )
            self._md = MarkItDown(docintel_endpoint=endpoint or None)
        else:
            self._md = MarkItDown()

    def extract(self, file_path: Path) -> tuple[str, str | None]:
        """파일을 Markdown으로 변환한다.

        Args:
            file_path: 변환할 파일 경로.

        Returns:
            (markdown_text, title) 튜플.
            title은 문서에 제목이 없으면 None.

        Raises:
            Exception: MarkItDown 변환 실패 시.
        """
        result = self._md.convert(str(file_path))
        text = result.text_content or ""
        title = getattr(result, "title", None)
        return text, title

    @staticmethod
    def _build_llm_client(cfg: dict):
        """OCR 모드용 LLM 클라이언트를 생성한다.

        환경변수 F2MD_LLM_API_KEY에서 API 키를 읽는다.

        Returns:
            OpenAI 클라이언트 객체, 키 없으면 None.
        """
        api_key = os.environ.get("F2MD_LLM_API_KEY")
        if not api_key:
            return None
        try:
            import openai

            return openai.OpenAI(api_key=api_key)
        except ImportError:
            return None
