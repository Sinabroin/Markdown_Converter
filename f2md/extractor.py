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

        # Local-first security guard: cloud integrations require explicit opt-in.
        if mode in ("ocr", "high_accuracy") and not self.cfg.get("security", {}).get(
            "allow_cloud_processing", False
        ):
            raise PermissionError(
                f"Cloud mode {mode!r} is disabled. Set security.allow_cloud_processing "
                "to true or pass --allow-cloud for an explicitly authorized run."
            )

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
        """Run local PaddleOCR on an image or a scanned PDF.

        PaddleOCR 3.x can process PDF files page by page with predict().
        Legacy 2.x OCR remains supported for images only.
        """
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise ImportError(
                "PaddleOCR is required for local OCR. Install paddleocr and paddlepaddle."
            ) from exc

        lang = self._paddle_cfg.get("lang", "korean")
        orientation = self._paddle_cfg.get("use_angle_cls", True)
        is_pdf = file_path.suffix.lower() == ".pdf"

        if hasattr(PaddleOCR, "predict"):
            # PaddleOCR 3.x API. It accepts local image and PDF paths.
            engine = PaddleOCR(
                lang=lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=orientation,
            )
            results = engine.predict(str(file_path))
            pages = []
            for index, result in enumerate(results or [], start=1):
                payload = self._paddle_result_payload(result)
                texts = payload.get("rec_texts", [])
                content = "\n\n".join(str(value).strip() for value in texts if str(value).strip())
                if content:
                    pages.append(f"## Page {index}\n\n{content}" if is_pdf else content)
            return "\n\n".join(pages), None

        # PaddleOCR 2.x does not provide a stable multi-page PDF API.
        if is_pdf:
            raise RuntimeError(
                "Local OCR of scanned PDFs requires PaddleOCR 3.x. "
                "Upgrade paddleocr or use a text-based PDF with standard mode."
            )
        engine = PaddleOCR(lang=lang, use_angle_cls=orientation, show_log=False)
        results = engine.ocr(str(file_path), cls=orientation)
        texts = []
        for page in results or []:
            for item in page or []:
                if not item or len(item) < 2:
                    continue
                info = item[1]
                if isinstance(info, (tuple, list)) and info and str(info[0]).strip():
                    texts.append(str(info[0]).strip())
        return "\n\n".join(texts), None

    @staticmethod
    def _paddle_result_payload(result) -> dict:
        """Handle PaddleOCR 3.x result objects and JSON/dict variants."""
        if isinstance(result, dict):
            data = result
        else:
            data = getattr(result, "json", None)
            if callable(data):
                data = data()
            if not isinstance(data, dict):
                # Some PaddleOCR result wrappers expose mapping methods.
                try:
                    data = dict(result)
                except (TypeError, ValueError):
                    raise TypeError("Unexpected PaddleOCR 3.x prediction output") from None
        payload = data.get("res", data)
        if not isinstance(payload, dict):
            raise TypeError("Unexpected PaddleOCR prediction payload")
        return payload

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
