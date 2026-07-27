import logging
from parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)

class TextParser(BaseParser):
    def parse(self, file_path: str):
        content = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read().strip()
                if text:
                    content.append((1, text))
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
        return content
