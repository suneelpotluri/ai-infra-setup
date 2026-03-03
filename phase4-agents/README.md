# Phase 4 — Agentic AI System

## Status: ✅ Complete

## What Was Built
An AI agent that uses Mistral 7B to:
1. Understand natural language questions
2. Dynamically fetch live infrastructure topology
3. Select the right tools automatically
4. Run live queries against PostgreSQL, MongoDB and servers
5. Generate human-readable answers

## Architecture
```
User Question
      ↓
Live Topology (infra_context.py)
      ↓
Mistral 7B selects tools
      ↓
┌─────────────────────────────┐
│ pg_tool.py   — PostgreSQL   │
│ mongo_tool.py — MongoDB     │
│ loki_tool.py  — Logs        │
│ system_tool.py — CPU/Mem    │
└─────────────────────────────┘
      ↓
Mistral 7B generates answer
```

## Files
- `agent.py` — Main agent
- `pg_tool.py` — PostgreSQL live queries
- `mongo_tool.py` — MongoDB live queries
- `loki_tool.py` — Loki log fetching
- `system_tool.py` — SSH-based system metrics
- `infra_context.py` — Live topology fetcher

## Example Questions
- "What is the current primary in ppg-cluster?"
- "Are there any errors in my databases?"
- "Give me a full health check of all databases"
- "Get CPU usage on all servers as a report"
- "Is there any replication lag?"
- "Are there any slow queries in PostgreSQL?"
- "How many connections does MongoDB have?"

## Key Design Decisions
- Uses OllamaLLM (not ChatOllama) — Mistral 7B doesn't support native tool calling
- Custom ReAct pattern via prompting instead of LangGraph tool binding
- Live topology fetched on every query — handles Patroni failover automatically
- SSH keys used for passwordless access to all servers
