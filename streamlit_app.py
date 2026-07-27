import streamlit as st
import os
from pathlib import Path
from config import DOCS_DIR
from ingest import ingest_directory
from query_engine import query_pipeline
from database import get_connection

# Page Configuration
st.set_page_config(
    page_title="Multi-Modal Document AI Pipeline",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Multi-Modal Document AI Search & Query Pipeline")
st.markdown("Upload PDFs, Word docs, PowerPoint presentations, Markdown, or scanned images and query them with SQL & AI.")

# Sidebar for Document Management
with st.sidebar:
    st.header("📂 Document Management")
    st.markdown("Upload files to ingest into the SQLite search database:")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "pptx", "md", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if st.button("🚀 Process & Ingest Files", type="primary"):
        if uploaded_files:
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
            for uploaded_file in uploaded_files:
                save_path = DOCS_DIR / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Saved: {uploaded_file.name}")
            
            with st.spinner("Parsing and indexing documents into SQLite..."):
                ingest_directory()
            st.success("All documents ingested successfully!")
        else:
            st.warning("Please upload at least one file first.")

    st.divider()
    st.subheader("📊 Indexed Database Stats")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = cursor.fetchone()[0]
        conn.close()
        st.metric("Documents Ingested", doc_count)
        st.metric("Total Text Chunks", chunk_count)
    except Exception:
        st.write("Database not initialized yet.")

# Main Chat Interface
st.subheader("💬 Ask Your Documents")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Box
if prompt := st.chat_input("Ask any question about your documents..."):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Searching SQLite & synthesizing answer..."):
            response = query_pipeline(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
