import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "sample_docs"
PARSERS_DIR = BASE_DIR / "parsers"

# SQLite Database Location
DB_PATH = DATA_DIR / "documents.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)
# LLM Configuration (Default: Gemini Free Tier or Local Ollama)
# You can set GEMINI_API_KEY as an environment variable or leave blank for Ollama
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()  # 'gemini' or 'ollama'
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
