import os
import logging
from pathlib import Path
from config import DOCS_DIR
from database import init_db, add_document, add_chunks
from parsers.parser_factory import get_parser_for_file

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logger = logging.getLogger(__name__)

def chunk_text(page_num: int, text: str, max_words: int = 400) -> list[tuple[int, str]]:
    """Splits large page text into smaller search chunks."""
    words = text.split()
    if len(words) <= max_words:
        return [(page_num, text)]
    
    chunks = []
    for i in range(0, len(words), max_words):
        chunk_str = " ".join(words[i:i + max_words])
        chunks.append((page_num, chunk_str))
    return chunks

def ingest_directory(directory_path: str = None):
    """Scans target directory, parses files, and indexes into SQLite."""
    init_db()

    target_dir = Path(directory_path) if directory_path else DOCS_DIR
    if not target_dir.exists():
        logger.error(f"Directory not found: {target_dir}")
        return

    files = [f for f in target_dir.rglob("*") if f.is_file()]
    if not files:
        logger.info(f"No files found in {target_dir}. Place sample files (.pdf, .docx, .pptx, .md, .png) here!")
        return

    logger.info(f"Found {len(files)} file(s) in {target_dir}. Starting ingestion pipeline...")

    processed_count = 0
    for file_path in files:
        parser = get_parser_for_file(str(file_path))
        if not parser:
            logger.warning(f"Skipping unsupported file format: {file_path.name}")
            continue

        logger.info(f"Processing: {file_path.name}")
        pages = parser.parse(str(file_path))
        if not pages:
            logger.warning(f"No text extracted from {file_path.name}")
            continue

        ext = file_path.suffix.lower()
        doc_id = add_document(
            filename=file_path.name,
            file_type=ext,
            filepath=str(file_path.resolve()),
            total_pages=len(pages)
        )

        all_chunks = []
        chunk_idx = 0
        for page_num, text in pages:
            split_chunks = chunk_text(page_num, text)
            for p_num, c_text in split_chunks:
                all_chunks.append((chunk_idx, p_num, c_text))
                chunk_idx += 1

        add_chunks(doc_id, file_path.name, all_chunks)
        processed_count += 1
        logger.info(f"Indexed {file_path.name} ({len(all_chunks)} chunks).")

    logger.info(f"Ingestion complete! Successfully indexed {processed_count} file(s).")

if __name__ == "__main__":
    ingest_directory()
