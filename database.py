import sqlite3
import logging
from pathlib import Path
from config import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection(read_only=False):
    """Establishes SQLite connection. Supports read-only mode for query safety."""
    if read_only:
        db_uri = f"file:{DB_PATH.resolve()}?mode=ro"
        return sqlite3.connect(db_uri, uri=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes SQLite tables including FTS5 Virtual Table for full-text search."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Documents Metadata Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL UNIQUE,
        file_type TEXT NOT NULL,
        total_pages INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Document Chunks Table (stores text by page/slide/section)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        page_number INTEGER DEFAULT 1,
        content TEXT NOT NULL,
        FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """)

    # 3. FTS5 Virtual Table for Lightning-Fast Keyword Search
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
        content,
        filename,
        page_number UNINDEXED,
        chunk_id UNINDEXED
    );
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized successfully at {DB_PATH}")

def add_document(filename: str, file_type: str, filepath: str, total_pages: int = 1) -> int:
    """Inserts document metadata or returns existing document ID if already ingested."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM documents WHERE filepath = ?", (filepath,))
    row = cursor.fetchone()
    if row:
        doc_id = row[0]
        # Clear existing chunks for re-ingestion
        cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
        conn.commit()
    else:
        cursor.execute(
            "INSERT INTO documents (filename, file_type, filepath, total_pages) VALUES (?, ?, ?, ?)",
            (filename, file_type, filepath, total_pages)
        )
        doc_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return doc_id

def add_chunks(doc_id: int, filename: str, chunks: list[tuple[int, int, str]]):
    """
    Inserts chunks into `document_chunks` and populates `document_fts`.
    chunks format: [(chunk_index, page_number, content)]
    """
    conn = get_connection()
    cursor = conn.cursor()

    for chunk_index, page_number, content in chunks:
        if not content.strip():
            continue
        cursor.execute(
            "INSERT INTO document_chunks (document_id, chunk_index, page_number, content) VALUES (?, ?, ?, ?)",
            (doc_id, chunk_index, page_number, content)
        )
        chunk_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO document_fts (content, filename, page_number, chunk_id) VALUES (?, ?, ?, ?)",
            (content, filename, str(page_number), str(chunk_id))
        )

    conn.commit()
    conn.close()

def execute_read_only_query(sql_query: str) -> tuple[list[str], list[tuple]]:
    """Executes a SQL SELECT query safely and returns (columns, rows)."""
    conn = get_connection(read_only=False)
    cursor = conn.cursor()
    
    # Safety Check: Only allow SELECT queries
    sql_stripped = sql_query.strip().upper()
    if not sql_stripped.startswith("SELECT") and not sql_stripped.startswith("WITH"):
        raise ValueError("Security violation: Only SELECT queries are permitted.")
        
    cursor.execute(sql_query)
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    conn.close()
    return columns, rows

def fts_search(query_term: str, limit: int = 10):
    """Direct Full-Text Search helper with query term sanitization and auto-init."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Extract clean words for FTS5 matching
    words = [f'"{w}"' for w in query_term.replace("?", "").replace('"', '').split() if w.isalnum()]
    if not words:
        conn.close()
        return []
        
    fts_query = " OR ".join(words)
    try:
        cursor.execute(
            "SELECT filename, page_number, content FROM document_fts WHERE document_fts MATCH ? LIMIT ?",
            (fts_query, limit)
        )
        results = cursor.fetchall()
    except Exception as e:
        logger.warning(f"FTS search exception: {e}")
        results = []
    finally:
        conn.close()

    return results

if __name__ == "__main__":
    init_db()
