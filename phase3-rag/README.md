# Phase 3 — RAG Pipeline

## Status: ✅ Complete

## What Was Built
A RAG (Retrieval Augmented Generation) pipeline that:
1. Fetches logs from Loki (PostgreSQL + MongoDB)
2. Embeds them using nomic-embed-text via Ollama
3. Stores embeddings in ChromaDB
4. Answers natural language questions using Mistral 7B

## Components
| Component | Purpose |
|---|---|
| nomic-embed-text | Convert logs to vector embeddings |
| ChromaDB | Vector store for similarity search |
| Mistral 7B Q4_K_M | LLM for answer generation |
| LangChain | Orchestration framework |

## Files
- `ingest_logs.py` — Fetches logs from Loki and stores in ChromaDB
- `query.py` — Interactive query interface
- `requirements.txt` — Python dependencies

## Usage
```bash
# Activate virtual environment
source venv/bin/activate

# Ingest latest logs
python ingest_logs.py

# Query your infrastructure
python query.py
```

## Example Queries
- "Are there any errors in PostgreSQL logs?"
- "What is the replication status of ppg-cluster?"
- "Are there any slow queries in the database?"
- "What MongoDB operations were logged recently?"

## Key Lessons Learned
- langchain.schema moved to langchain_core.documents
- langchain.prompts moved to langchain_core.prompts
- RetrievalQA deprecated — use LCEL (LangChain Expression Language) instead
- Always pin package versions in requirements.txt
