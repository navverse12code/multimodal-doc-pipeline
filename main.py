import sys
import sqlite3

# Ensure UTF-8 encoding in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from ingest import ingest_directory
from query_engine import query_pipeline
from database import get_connection

def print_banner():
    print("=" * 65)
    print(" 🚀 MULTI-MODAL DOCUMENT INGESTION & SQL-LLM QUERY PIPELINE")
    print("    Supported: .pdf, .docx, .pptx, .md, .txt, .png, .jpg")
    print("=" * 65)

def print_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM document_chunks")
    chunk_count = cursor.fetchone()[0]
    conn.close()

    print(f"\n📊 Current Database Stats: {doc_count} document(s), {chunk_count} chunk(s) indexed.")

def main():
    print_banner()
    
    # Auto-ingest default sample docs if DB is empty
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        print("\n📥 Initializing and indexing documents in sample_docs/...")
        ingest_directory()

    print_stats()

    while True:
        print("\nCommands:")
        print(" [1] Ask a question")
        print(" [2] Ingest / Re-index documents")
        print(" [3] View database stats")
        print(" [4] Exit")
        
        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            question = input("\n❓ Enter your question: ").strip()
            if question:
                print("\n🔍 Searching SQLite database and generating answer...")
                answer = query_pipeline(question)
                print("\n💡 ANSWER:")
                print(answer)
        elif choice == "2":
            custom_path = input("\nEnter folder path (or press Enter for sample_docs/): ").strip()
            ingest_directory(custom_path if custom_path else None)
            print_stats()
        elif choice == "3":
            print_stats()
        elif choice == "4" or choice.lower() == "exit":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
