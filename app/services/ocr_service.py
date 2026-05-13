from PIL import Image
import pytesseract
from pathlib import Path
from typing import Optional
import os


class OCRService:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            pytesseract.pytesseract.tesseract_cmd = (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            )

    def extract_text_from_image(self, image_path: str) -> str:
        try:
            image = Image.open(image_path)

            if image.mode != "RGB":
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image, lang="chi_sim+eng")

            return text.strip()
        except Exception as e:
            print(f"OCR提取失败 {image_path}: {e}")
            return ""

    def extract_text_from_image_file(self, image_data: bytes) -> str:
        try:
            from io import BytesIO

            image = Image.open(BytesIO(image_data))

            if image.mode != "RGB":
                image = image.convert("RGB")

            text = pytesseract.image_to_string(image, lang="chi_sim+eng")

            return text.strip()
        except Exception as e:
            print(f"OCR提取失败: {e}")
            return ""


ocr_service = OCRService()
