"""
Phase 3 - RAG Query Interface
Ask natural language questions about your infrastructure logs
"""

from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# ── Config ────────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434"
COLLECTION  = "infra_logs"

# ── Setup ─────────────────────────────────────────────────
def setup_rag():
    print("🔧 Setting up embeddings...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=OLLAMA_URL
    )

    print("🔧 Connecting to ChromaDB...")
    vectorstore = Chroma(
        collection_name=COLLECTION,
        embedding_function=embeddings,
        persist_directory="./chroma_store"
    )

    print("🔧 Loading Mistral 7B...")
    llm = OllamaLLM(
        model="mistral:7b-instruct-q4_K_M",
        base_url=OLLAMA_URL,
        temperature=0.1
    )

    prompt = PromptTemplate(
        template="""You are an expert DBA and infrastructure engineer.
Use the following log entries to answer the question.
Be specific and reference actual log content when possible.
If you cannot find relevant information, say so clearly.

Log Context:
{context}

Question: {question}

Answer:""",
        input_variables=["context", "question"]
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 10}
    )

    def format_docs(docs):
        return "\n\n".join([
            f"[{d.metadata.get('host','?')} | {d.metadata.get('timestamp','?')}]\n{d.page_content}"
            for d in docs
        ])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever

# ── Query ─────────────────────────────────────────────────
def query_infra(chain, retriever, question):
    print(f"\n🔍 Question: {question}")
    print("⏳ Thinking...")

    answer = chain.invoke(question)

    print(f"\n💡 Answer:\n{answer}")

    # Show source docs
    docs = retriever.invoke(question)
    print(f"\n📚 Sources ({len(docs)} log entries used):")
    for i, doc in enumerate(docs[:3], 1):
        meta = doc.metadata
        print(f"   [{i}] {meta.get('host','?')} | {meta.get('timestamp','?')}")
        print(f"        {doc.page_content[:120]}...")

    return answer

# ── Main ──────────────────────────────────────────────────
def main():
    print("🤖 AI Infrastructure Query System")
    print("=" * 50)

    chain, retriever = setup_rag()

    print("\n✅ Ready! Type your questions (or 'quit' to exit)")
    print("\n💡 Example questions:")
    examples = [
        "Are there any errors in PostgreSQL logs?",
        "What is the replication status of ppg-cluster?",
        "Are there any slow queries in the database?",
        "What MongoDB operations were logged recently?",
    ]
    for i, q in enumerate(examples, 1):
        print(f"   {i}. {q}")
    print()

    while True:
        question = input("Ask a question: ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if not question:
            continue
        query_infra(chain, retriever, question)
        print("\n" + "─" * 50)

if __name__ == "__main__":
    main()
