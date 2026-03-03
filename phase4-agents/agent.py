"""
Phase 4 - AI Infrastructure Agent
Uses live topology + Mistral 7B to answer infrastructure questions
"""

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from infra_context import get_live_context
import pg_tool
import mongo_tool
import loki_tool
import system_tool
import re

# ── Tool Registry ─────────────────────────────────────────
TOOLS = {
    "pg_replication":  ("Check PostgreSQL replication status and lag",         pg_tool.get_replication_status),
    "pg_connections":  ("Get active PostgreSQL connections and queries",        pg_tool.get_active_connections),
    "pg_slow_queries": ("Get slow queries from pg_stat_statements",            pg_tool.get_slow_queries),
    "pg_db_sizes":     ("Get PostgreSQL database sizes",                       pg_tool.get_database_sizes),
    "pg_locks":        ("Check for PostgreSQL locks and blocking queries",     pg_tool.get_locks),
    "mongo_status":    ("Get MongoDB server status, connections and memory",   mongo_tool.get_server_status),
    "mongo_databases": ("List MongoDB databases with sizes",                   mongo_tool.get_databases),
    "mongo_slow_ops":  ("Check for slow MongoDB operations",                   mongo_tool.get_slow_operations),
    "mongo_replica":   ("Get MongoDB replica set status",                      mongo_tool.get_replica_status),
    "pg_logs":         ("Fetch recent PostgreSQL logs from Loki",              lambda: loki_tool.fetch_recent_logs("postgresql", minutes=30, limit=20)),
    "mongo_logs":      ("Fetch recent MongoDB logs from Loki",                 lambda: loki_tool.fetch_recent_logs("mongodb", minutes=30, limit=20)),
    "pg_errors":       ("Check PostgreSQL logs for errors and warnings",       lambda: loki_tool.fetch_errors("postgresql", minutes=60)),
    "mongo_errors":    ("Check MongoDB logs for errors and warnings",          lambda: loki_tool.fetch_errors("mongodb", minutes=60)),
    "all_servers_report": ("Get CPU, memory and disk report for ALL servers",  system_tool.get_all_servers_report),
}

def tools_description():
    return "\n".join([f"- {name}: {desc}" for name, (desc, _) in TOOLS.items()])

# ── LLM Setup ─────────────────────────────────────────────
def get_llm():
    return OllamaLLM(
        model="mistral:7b-instruct-q4_K_M",
        base_url="http://localhost:11434",
        temperature=0.1
    )

# ── Prompts ───────────────────────────────────────────────
PLAN_PROMPT = PromptTemplate(
    template="""You are an expert DBA and infrastructure engineer.

Current Infrastructure Status:
{context}

Given a question, select the most relevant tools to answer it.

Available tools:
{tools}

Question: {question}

Reply with ONLY a comma-separated list of tool names to use.
Example: pg_replication,pg_logs

Tools to use:""",
    input_variables=["context", "tools", "question"]
)

ANSWER_PROMPT = PromptTemplate(
    template="""You are an expert DBA and infrastructure engineer.

Current Infrastructure Status:
{context}

Real-time data collected from infrastructure:
{data}

Question: {question}

Provide a clear, detailed answer based on the live data above:""",
    input_variables=["context", "data", "question"]
)

# ── Agent ─────────────────────────────────────────────────
def ask_agent(question: str):
    llm = get_llm()

    print(f"\n🔍 Question: {question}")

    # Get LIVE context every time — handles failover!
    print("🔄 Fetching live infrastructure topology...")
    context = get_live_context()

    print("⏳ Selecting tools...")

    # Step 1 — Pick tools
    plan_chain = PLAN_PROMPT | llm | StrOutputParser()
    tool_response = plan_chain.invoke({
        "context":  context,
        "tools":    tools_description(),
        "question": question
    })

    # Parse tool names
    selected = [t.strip() for t in re.split(r"[,\n]", tool_response)
                if t.strip() in TOOLS]

    if not selected:
        selected = ["pg_replication", "mongo_status"]

    print(f"🔧 Using tools: {', '.join(selected)}")

    # Step 2 — Run tools
    data_parts = []
    for tool_name in selected:
        print(f"   Running {tool_name}...")
        _, fn = TOOLS[tool_name]
        result = fn()
        data_parts.append(f"=== {tool_name} ===\n{result}")

    all_data = "\n\n".join(data_parts)

    # Step 3 — Generate answer
    print("💭 Generating answer...")
    answer_chain = ANSWER_PROMPT | llm | StrOutputParser()
    answer = answer_chain.invoke({
        "context":  context,
        "data":     all_data,
        "question": question
    })

    print(f"\n💡 Answer:\n{answer}")
    print(f"\n📊 Data sources used: {', '.join(selected)}")

    return answer

# ── Main ─────────────────────────────────────────────────
def main():
    print("🤖 AI Infrastructure Agent")
    print("=" * 50)
    print("✅ Agent ready! (Mistral 7B + Live Topology)\n")

    print("💡 Example questions:")
    examples = [
        "What is the pg1 node and its current role?",
        "Which node is the primary in ppg-cluster?",
        "What is the replication status of PostgreSQL?",
        "Are there any errors in my databases?",
        "Give me a full health check of all databases",
        "Is there any replication lag?",
        "How many connections does MongoDB have?",
    ]
    for i, q in enumerate(examples, 1):
        print(f"   {i}. {q}")
    print()

    while True:
        question = input("Ask a question (or 'quit'): ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if not question:
            continue
        ask_agent(question)
        print("\n" + "─" * 50)

if __name__ == "__main__":
    main()
