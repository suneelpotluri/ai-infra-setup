# Setup Progress Log

## Phase 1 — Central AI Server ✅ Complete
**Date Completed:** February 28, 2026

### Completed Steps
- [x] WSL2 Ubuntu 22.04 installed on Windows
- [x] WSL2 moved to F: drive (SanDisk SSD, 1.8TB free)
- [x] NVIDIA RTX 3060 GPU passthrough working in WSL2
- [x] CUDA 12.7 toolkit installed
- [x] nvidia-smi symlinked from /usr/lib/wsl/lib/
- [x] Ollama installed and running as systemd service
- [x] Ollama configured to listen on 0.0.0.0:11434 (all interfaces)
- [x] mistral:7b-instruct-q4_K_M model downloaded (4.4GB)
- [x] nomic-embed-text model downloaded (274MB)
- [x] Docker CE installed in WSL2
- [x] Open WebUI running on port 3000
- [x] Open WebUI connected to Ollama via WSL2 IP (172.21.47.67:11434)
- [x] Successfully chatting with local LLM!

### Key Configuration Notes
- WSL2 IP: 172.21.47.67 (may change on restart — check with `hostname -I`)
- Ollama service: `sudo systemctl status ollama`
- Open WebUI: http://localhost:3000
- Models stored at: ~/.ollama/models (inside ext4.vhdx on F: drive)
- WSL2 disk: F:\WSL\Ubuntu2204\ext4.vhdx

### Lessons Learned
- Do NOT install nvidia-utils from Ubuntu repos in WSL2 — use CUDA repo instead
- nvidia-smi in WSL2 lives at /usr/lib/wsl/lib/ not standard path
- Ollama default listens on 127.0.0.1 — must override to 0.0.0.0 for Docker/network access
- Use --network host causes issues in WSL2 Docker — use explicit -p port mapping instead
- After WSL2 import, default user resets to root — fix with /etc/wsl.conf

---

## Phase 2 — Log Collection 🔜 Not Started
**Target:** Ship logs from all VMs to central Loki

### Prerequisites Needed
- [ ] Note down all VM IPs
- [ ] Ensure network connectivity between laptop and all VMs
- [ ] Open firewall ports on RHEL VMs (9080, 3100)

---

## Phase 3 — RAG Pipeline 🔜 Not Started
**Target:** Embed logs into ChromaDB for semantic search

---

## Phase 4 — Agentic System 🔜 Not Started
**Target:** LangGraph agent with tools for each infrastructure component

---

## Phase 5 — Automation 🔜 Not Started
**Target:** Scheduled ingestion + daily health summaries
