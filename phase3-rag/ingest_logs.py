"""
Phase 3 - Log Ingestion Pipeline
Fetches logs from Loki and stores embeddings in ChromaDB
"""

import requests
import time
from datetime import datetime, timedelta
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ── Config ────────────────────────────────────────────────
LOKI_URL     = "http://localhost:3100"
CHROMA_URL   = "http://localhost:8000"
OLLAMA_URL   = "http://localhost:11434"
COLLECTION   = "infra_logs"

# Jobs to ingest
JOBS = ["postgresql", "mongodb"]
CLUSTER = "ppg-cluster"

# ── Fetch logs from Loki ──────────────────────────────────
def fetch_logs(job, hours=24, limit=500):
    end   = int(time.time() * 1e9)
    start = int((time.time() - hours * 3600) * 1e9)

    if job == "postgresql":
        query = f'{{job="{job}", cluster="{CLUSTER}"}}'
    else:
        query = f'{{job="{job}"}}'

    resp = requests.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params={
            "query": query,
            "start": start,
            "end":   end,
            "limit": limit,
            "direction": "backward"
        }
    )

    if resp.status_code != 200:
        print(f"❌ Loki error for {job}: {resp.text}")
        return []

    results = resp.json().get("data", {}).get("result", [])
    docs = []

    for stream in results:
        labels = stream.get("stream", {})
        for ts, line in stream.get("values", []):
            # Convert nanosecond timestamp
            dt = datetime.fromtimestamp(int(ts) / 1e9)
            docs.append(Document(
                page_content=line,
                metadata={
                    "job":       job,
                    "host":      labels.get("host", "unknown"),
                    "cluster":   labels.get("cluster", "unknown"),
                    "role":      labels.get("role", "unknown"),
                    "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "source":    "loki"
                }
            ))

    print(f"✅ Fetched {len(docs)} log entries for job={job}")
    return docs

# ── Store in ChromaDB ─────────────────────────────────────
def ingest():
    print("🚀 Starting log ingestion pipeline...")
    print(f"   Loki:    {LOKI_URL}")
    print(f"   Chroma:  {CHROMA_URL}")
    print(f"   Ollama:  {OLLAMA_URL}")
    print()

    # Setup embeddings
    print("🔧 Initialising embeddings (nomic-embed-text)...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_URL
    )

    # Setup ChromaDB
    vectorstore = Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory="./chroma_store"
    )

    # Fetch and ingest each job
    all_docs = []
    for job in JOBS:
        print(f"\n📥 Fetching logs for job={job}...")
        docs = fetch_logs(job, hours=24, limit=200)
        all_docs.extend(docs)

    if not all_docs:
        print("❌ No logs fetched — check Loki connection")
        return

    print(f"\n📦 Total documents to embed: {len(all_docs)}")
    print("⏳ Embedding and storing in ChromaDB (this takes a few minutes)...")

    # Store in batches
    batch_size = 50
    for i in range(0, len(all_docs), batch_size):
        batch = all_docs[i:i+batch_size]
        vectorstore.add_documents(batch)
        print(f"   Stored batch {i//batch_size + 1}/{(len(all_docs)-1)//batch_size + 1}")

    print(f"\n✅ Ingestion complete!")
    print(f"   Total documents stored: {len(all_docs)}")
    print(f"   Collection: {COLLECTION}")
    print(f"   Storage: ./chroma_store")

if __name__ == "__main__":
    ingest()
