import os
from parsers.pdf_parser import PDFParser
from parsers.docx_parser import DocxParser
from parsers.pptx_parser import PPTXParser
from parsers.text_parser import TextParser
from parsers.image_parser import ImageParser

PARSER_MAP = {
    ".pdf": PDFParser(),
    ".docx": DocxParser(),
    ".doc": DocxParser(),
    ".pptx": PPTXParser(),
    ".ppt": PPTXParser(),
    ".md": TextParser(),
    ".txt": TextParser(),
    ".csv": TextParser(),
    ".json": TextParser(),
    ".png": ImageParser(),
    ".jpg": ImageParser(),
    ".jpeg": ImageParser(),
    ".tiff": ImageParser(),
    ".bmp": ImageParser()
}

def get_parser_for_file(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    return PARSER_MAP.get(ext)
