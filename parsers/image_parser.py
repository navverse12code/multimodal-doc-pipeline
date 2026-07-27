import logging
from PIL import Image
import pytesseract
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class ImageParser(BaseParser):
    def parse(self, file_path: str):
        content = []
        try:
            img = Image.open(file_path)
            try:
                ocr_text = pytesseract.image_to_string(img).strip()
            except Exception as ocr_err:
                logger.warning(f"OCR tool error for image {file_path}: {ocr_err}")
                ocr_text = f"[Image File: {file_path} - Install Tesseract OCR for text extraction]"

            if ocr_text:
                content.append((1, ocr_text))
        except Exception as e:
            logger.error(f"Error reading image {file_path}: {e}")
        return content
