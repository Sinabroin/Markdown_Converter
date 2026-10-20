"""Real-model OCR smoke test using a generated, non-confidential scanned PDF.

Run with:
  pip install paddlepaddle==3.2.0 paddleocr==3.2.0 pillow pymupdf
  python scripts/smoke_test_real_ocr.py
"""

from pathlib import Path
import tempfile

import fitz
from PIL import Image, ImageDraw, ImageFont

from f2md.extractor import Extractor


def make_scanned_pdf(path: Path) -> None:
    pages = ["INVOICE NUMBER 12345", "SECOND SCANNED PAGE 67890"]
    doc = fitz.open()
    for value in pages:
        image = Image.new("RGB", (1300, 480), "white")
        draw = ImageDraw.Draw(image)
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font = ImageFont.truetype(font_path, 67)
        draw.text((55, 170), value, font=font, fill="black")

        with tempfile.NamedTemporaryFile(suffix=".png") as png:
            image.save(png.name)
            page = doc.new_page(width=650, height=240)
            page.insert_image(page.rect, filename=png.name)
    doc.save(path)
    doc.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "synthetic_scanned.pdf"
        make_scanned_pdf(pdf_path)
        doc = fitz.open(pdf_path)
        assert len(doc) == 2
        assert all(not page.get_text().strip() for page in doc), "PDF must be image-only"
        doc.close()

        text, _ = Extractor(
            mode="paddle_ocr",
            cfg={"paddle_ocr": {"lang": "en", "use_angle_cls": False}},
        ).extract(pdf_path)

        print("OCR OUTPUT:\n" + text)
        assert "## Page 1" in text and "## Page 2" in text, (
            "Expected OCR to read both pages"
        )
        recognized = "".join(text.split())
        assert len(recognized) >= 30, "OCR returned too little text"


if __name__ == "__main__":
    main()
