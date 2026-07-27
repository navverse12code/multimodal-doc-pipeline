import fitz  # PyMuPDF
import logging
from PIL import Image
import io
import pytesseract
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class PDFParser(BaseParser):
    def parse(self, file_path: str):
        pages = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")

                # Fallback to OCR if page has no extracted text (scanned image PDF page)
                if not text.strip():
                    logger.info(f"Page {page_num+1} in {file_path} appears scanned. Running OCR...")
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_bytes))
                    try:
                        text = pytesseract.image_to_string(img)
                    except Exception as ocr_err:
                        logger.warning(f"OCR failed for page {page_num+1}: {ocr_err}")
                        text = "[Scanned Page - OCR Unavailable]"

                if text.strip():
                    pages.append((page_num + 1, text.strip()))

            doc.close()
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
        
        return pages
