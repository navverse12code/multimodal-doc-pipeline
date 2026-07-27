import os
import sys
import logging
import requests
import sqlite3

# Ensure UTF-8 encoding in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from config import GEMINI_API_KEY, OLLAMA_HOST, OLLAMA_MODEL, LLM_PROVIDER
from database import execute_read_only_query, fts_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System Prompt exposing SQLite Schema to LLM
SYSTEM_SCHEMA_PROMPT = """
You are an expert Data & Search Assistant with access to a SQLite database containing multi-modal document chunks.

Database Schema:
1. documents (id, filename, file_type, filepath, total_pages)
2. document_chunks (id, document_id, chunk_index, page_number, content)
3. document_fts (content, filename, page_number, chunk_id) -- SQLite FTS5 Virtual Table for full-text search. Use MATCH syntax. Example: SELECT filename, page_number, content FROM document_fts WHERE document_fts MATCH 'keyword' LIMIT 5;

Your task:
When the user asks a question, write a single valid SQLite SELECT query to retrieve the most relevant information.
Return ONLY the raw SQL query without markdown code blocks, explanations, or quotes.
"""

def call_gemini(prompt: str) -> str:
    """Calls Gemini API (Free Tier)."""
    try:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        if not api_key or "AIzaSy" not in api_key or "." in api_key:
            logger.warning("Gemini API key is unconfigured or invalid. Falling back to SQLite search.")
            return ""
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini API request failed: {e}")
        return ""

def call_ollama(prompt: str) -> str:
    """Calls local Ollama API (100% Free & Offline)."""
    try:
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"Local Ollama call failed: {e}")
    return ""

def generate_llm_response(prompt: str) -> str:
    """Routes query to configured LLM (Gemini or Ollama)."""
    if LLM_PROVIDER == "gemini":
        res = call_gemini(prompt)
        if res:
            return res
    # Fallback to Ollama
    return call_ollama(prompt)

def query_pipeline(user_question: str) -> str:
    """
    Main RAG Pipeline:
    1. Ask LLM to write a SQL query based on user question.
    2. Run SQL against SQLite DB.
    3. Feed returned context back to LLM for final answer synthesis.
    """
    logger.info(f"User Query: {user_question}")

    # Step 1: Generate SQL via LLM
    sql_prompt = f"{SYSTEM_SCHEMA_PROMPT}\n\nUser Question: {user_question}\nGenerate SQL Query:"
    generated_sql = generate_llm_response(sql_prompt)

    rows = []
    columns = []

    # Clean SQL formatting if returned with ```sql wrappers
    if generated_sql:
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

    # Step 2: Try executing generated SQL
    if generated_sql and generated_sql.upper().startswith("SELECT"):
        logger.info(f"Executing LLM SQL: {generated_sql}")
        try:
            columns, rows = execute_read_only_query(generated_sql)
        except Exception as err:
            logger.warning(f"Generated SQL execution failed: {err}. Falling back to FTS search.")

    # Fallback if SQL generation fails or returns empty
    if not rows:
        search_terms = user_question.replace("'", "").replace('"', "")
        rows = fts_search(search_terms)
        columns = ["filename", "page_number", "content"]

    if not rows:
        # Smart fallback for general questions like "summarize the pdf"
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT documents.filename, document_chunks.page_number, document_chunks.content 
            FROM document_chunks 
            JOIN documents ON document_chunks.document_id = documents.id 
            LIMIT 5
        """)
        rows = cursor.fetchall()
        conn.close()

    if not rows:
        return "No relevant information found in the ingested documents."

    # Step 3: Format Context & Synthesize Answer
    context_str = ""
    for r in rows:
        if len(r) >= 3:
            context_str += f"\n---\nDocument: {r[0]} (Page/Slide: {r[1]})\nContent:\n{r[2]}\n"
        elif len(r) == 2:
            context_str += f"\n---\nDocument: {r[0]}\nContent:\n{r[1]}\n"

    final_prompt = f"""
You are a helpful assistant. Answer the user's question using ONLY the provided document context below.
Cite the source file names and page/slide numbers where relevant.

Context:
{context_str}

User Question: {user_question}

Answer:
"""
    answer = generate_llm_response(final_prompt)

    if not answer:
        # Fallback raw answer if LLM offline
        return f"Retrieved Document Snippets:\n{context_str}"

    return answer

if __name__ == "__main__":
    res = query_pipeline("What are the contract termination terms and license price?")
    print("\n--- QUERY RESULT ---")
    print(res)
