"""MarkItDown 래퍼 — standard / paddle_ocr / ocr / high_accuracy 4-way 모드."""

import os
from pathlib import Path


class Extractor:
    """MarkItDown 또는 PaddleOCR을 감싸는 변환 엔진.

    모드별 엔진 인스턴스를 생성하고 파일을 Markdown으로 변환한다.

    모드:
        standard      : MarkItDown 기본 변환
        paddle_ocr    : PaddleOCR 로컬 무료 OCR (API 키 불필요)
        ocr           : MarkItDown + OpenAI LLM Vision (API 키 필요)
        high_accuracy : MarkItDown + Azure Document Intelligence
    """

    def __init__(self, mode: str = "standard", cfg: dict | None = None):
        """Extractor를 초기화한다.

        Args:
            mode: 'standard', 'paddle_ocr', 'ocr', 'high_accuracy' 중 하나.
            cfg: settings.yaml 설정 딕셔너리. 각 모드 설정에 사용.
        """
        self.mode = mode
        self.cfg = cfg or {}
        self._md = None
        self._paddle_cfg = self.cfg.get("paddle_ocr", {})

        if mode == "paddle_ocr":
            pass  # PaddleOCR은 extract() 호출 시 지연 초기화
        elif mode == "ocr":
            from markitdown import MarkItDown
            llm_client = self._build_llm_client(self.cfg)
            llm_model = self.cfg.get("ocr", {}).get("llm_model", "gpt-4o")
            self._md = MarkItDown(
                enable_plugins=True,
                llm_client=llm_client,
                llm_model=llm_model,
            )
        elif mode == "high_accuracy":
            from markitdown import MarkItDown
            endpoint = os.environ.get(
                "F2MD_DOCINTEL_ENDPOINT",
                self.cfg.get("high_accuracy", {}).get("endpoint", ""),
            )
            self._md = MarkItDown(docintel_endpoint=endpoint or None)
        else:  # standard
            from markitdown import MarkItDown
            self._md = MarkItDown()

    def extract(self, file_path: Path) -> tuple[str, str | None]:
        """파일을 Markdown으로 변환한다.

        Args:
            file_path: 변환할 파일 경로.

        Returns:
            (markdown_text, title) 튜플.
            title은 문서에 제목이 없으면 None.

        Raises:
            Exception: 변환 실패 시.
        """
        if self.mode == "paddle_ocr":
            return self._extract_with_paddle(file_path)

        result = self._md.convert(str(file_path))
        text = result.text_content or ""
        title = getattr(result, "title", None)
        return text, title

    def _extract_with_paddle(self, file_path: Path) -> tuple[str, str | None]:
        """PaddleOCR로 이미지에서 텍스트를 추출해 Markdown 문자열로 반환한다.

        설정(paddle_ocr 섹션)에서 lang, use_angle_cls를 읽는다.
        모델은 첫 실행 시 자동 다운로드된다 (최초 1회, 약 500MB~1GB).

        Args:
            file_path: 이미지 파일 경로 (.jpg, .png, .tif 등).

        Returns:
            (markdown_text, None) 튜플. 제목 정보는 없으므로 None 반환.

        Raises:
            ImportError: paddleocr 패키지가 설치되지 않은 경우.
            Exception: OCR 처리 실패 시.
        """
        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise ImportError(
                "PaddleOCR이 설치되지 않았습니다. "
                "pip install paddlepaddle paddleocr 를 실행하세요."
            ) from e

        lang = self._paddle_cfg.get("lang", "korean")
        use_angle_cls = self._paddle_cfg.get("use_angle_cls", True)

        ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=lang,
            show_log=False,
        )

        result = ocr.ocr(str(file_path), cls=use_angle_cls)

        lines: list[str] = []
        for page in (result or []):
            for line in (page or []):
                # line 구조: [좌표 4점, (텍스트, 신뢰도)]
                if not line or len(line) < 2:
                    continue
                text_info = line[1]
                if not text_info:
                    continue
                text = text_info[0] if isinstance(text_info, (list, tuple)) else str(text_info)
                if text.strip():
                    lines.append(text.strip())

        markdown = "\n\n".join(lines)
        return markdown, None

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
