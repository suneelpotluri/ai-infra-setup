# 🤖 AI-Powered Infrastructure Query System

> A fully local, private AI system that integrates PostgreSQL, MongoDB, Kubernetes, and Ansible — powered by local LLMs via Ollama. No cloud, no API costs, 100% your data.

## 🖥️ Environment

| Component | Details |
|---|---|
| Central AI Server | Windows Laptop, 64GB RAM, NVIDIA RTX 3060 (6GB VRAM) |
| WSL2 | Ubuntu 22.04 on F: drive (SanDisk SSD) |
| PostgreSQL | 3-node cluster (primary + 2 replicas) |
| MongoDB | Standalone single node |
| Kubernetes | kubeadm on VMs |
| Ansible | Control node (RHEL/Rocky VM) |
| VM OS | Ubuntu/Debian + RHEL/CentOS/Rocky Linux |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WINDOWS LAPTOP (64GB RAM)                    │
│                                                                 │
│   WSL2 Ubuntu 22.04 (F: Drive - SanDisk SSD)                   │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Ollama          → Local LLM Engine  (port 11434)       │  │
│   │  Mistral 7B Q4   → Main LLM Model                       │  │
│   │  nomic-embed     → Embedding Model for RAG              │  │
│   │  Open WebUI      → Chat Interface    (port 3000)        │  │
│   │  ChromaDB        → Vector Store      (port 8000)        │  │
│   │  Loki            → Log Aggregation   (port 3100)        │  │
│   │  Grafana         → Visualization     (port 3001)        │  │
│   │  FastAPI         → AI REST API       (port 8080)        │  │
│   └─────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
┌───────▼──────┐   ┌────────▼──────┐   ┌────────▼──────┐
│  PostgreSQL  │   │  Kubernetes   │   │  MongoDB +    │
│  3-node      │   │  kubeadm      │   │  Ansible VM   │
│  Cluster     │   │  Cluster      │   │               │
│  Promtail ✓  │   │  Promtail     │   │  Promtail     │
│  (Ubuntu)    │   │  DaemonSet    │   │  (RHEL/Rocky) │
└──────────────┘   └───────────────┘   └───────────────┘
```

## 📋 Phases

| Phase | Description | Status |
|---|---|---|
| [Phase 1](./phase1-central-ai/) | Central AI Server Setup | ✅ Complete |
| [Phase 2](./phase2-log-collection/) | Log Collection (Loki + Promtail) | 🔜 Next |
| [Phase 3](./phase3-rag/) | RAG Pipeline (Embeddings + ChromaDB) | 🔜 Upcoming |
| [Phase 4](./phase4-agents/) | Agentic System (LangGraph Tools) | 🔜 Upcoming |
| [Phase 5](./phase5-automation/) | Automation & Scheduling | 🔜 Upcoming |

## 🚀 Quick Start

### Prerequisites
- Windows with WSL2 (Ubuntu 22.04)
- NVIDIA GPU with driver 525.60+
- Docker installed in WSL2

### Phase 1 — Get AI Running
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull mistral:7b-instruct-q4_K_M
ollama pull nomic-embed-text

# Launch Open WebUI
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

Open WebUI: http://localhost:3000

## 📁 Repository Structure

```
ai-infra-repo/
├── README.md                          # This file
├── docs/
│   ├── architecture.md                # Detailed architecture
│   └── progress.md                    # Setup progress log
├── phase1-central-ai/
│   ├── README.md                      # Phase 1 guide
│   ├── setup.sh                       # Automated setup script
│   └── ollama-service-override.conf   # Ollama systemd config
├── phase2-log-collection/
│   ├── README.md                      # Phase 2 guide
│   ├── loki/
│   │   ├── docker-compose.yml         # Loki + Grafana stack
│   │   └── loki-config.yml            # Loki configuration
│   └── promtail-configs/
│       ├── ubuntu-postgresql.yml      # Promtail for PG nodes
│       ├── rhel-ansible.yml           # Promtail for Ansible VM
│       ├── mongodb.yml                # Promtail for MongoDB
│       └── kubernetes-daemonset.yaml  # K8s Promtail DaemonSet
├── phase3-rag/
│   ├── README.md                      # Phase 3 guide
│   ├── requirements.txt               # Python dependencies
│   ├── log_ingestion.py               # Loki → ChromaDB pipeline
│   └── query.py                       # RAG query interface
├── phase4-agents/
│   ├── README.md                      # Phase 4 guide
│   ├── tools.py                       # Infrastructure tools
│   ├── agent.py                       # LangGraph agent
│   └── api/
│       └── main.py                    # FastAPI interface
├── phase5-automation/
│   ├── README.md                      # Phase 5 guide
│   └── daily_summary.py               # Daily health report
└── scripts/
    ├── wsl-setup.ps1                  # WSL2 setup (PowerShell)
    └── vm-firewall-setup.sh           # VM firewall rules
```

## 🔧 Services & Ports

| Service | Port | URL | Purpose |
|---|---|---|---|
| Ollama | 11434 | http://localhost:11434 | LLM Engine |
| Open WebUI | 3000 | http://localhost:3000 | Chat Interface |
| ChromaDB | 8000 | http://localhost:8000 | Vector Store |
| Loki | 3100 | http://localhost:3100 | Log Storage |
| Grafana | 3001 | http://localhost:3001 | Visualization |
| FastAPI | 8080 | http://localhost:8080 | AI REST API |

## 💬 Example Queries

Once fully set up, you can ask:
- *"Are there any slow queries on PostgreSQL right now?"*
- *"What is the replication lag on my PG cluster?"*
- *"Are there any failed pods in Kubernetes?"*
- *"Show me MongoDB errors from the last hour"*
- *"Did any Ansible playbooks fail today?"*
- *"Give me a complete health summary of all my systems"*

## 📚 Learning Alignment

This project directly applies the IBM RAG and Agentic AI Professional Certificate curriculum:

| Course Topic | Applied In |
|---|---|
| LLM fundamentals | Phase 1 — Ollama + Mistral |
| Vector databases | Phase 3 — ChromaDB |
| RAG pipelines | Phase 3 — Log embeddings |
| LangChain | Phase 3 & 4 |
| LangGraph agents | Phase 4 — Infrastructure agent |
| Agentic workflows | Phase 4 & 5 |
