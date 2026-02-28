#!/bin/bash
# =============================================================================
# Phase 1 Setup Script — AI Infrastructure System
# Run this inside WSL2 Ubuntu 22.04
# Usage: chmod +x setup.sh && ./setup.sh
# =============================================================================

set -e  # Exit on any error

echo "=============================================="
echo " AI Infrastructure System — Phase 1 Setup"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "🔧 $1"; }

# ─── Step 1: CUDA Repository ──────────────────────────────────────────────────
info "Setting up NVIDIA CUDA repository..."
wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update -qq
ok "CUDA repository added"

# ─── Step 2: CUDA Toolkit ─────────────────────────────────────────────────────
info "Installing CUDA toolkit..."
sudo apt-get install -y cuda-toolkit-12-3
ok "CUDA toolkit installed"

# ─── Step 3: CUDA PATH ────────────────────────────────────────────────────────
info "Configuring CUDA PATH..."
grep -qxF 'export PATH=/usr/local/cuda/bin:$PATH' ~/.bashrc || \
  echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
grep -qxF 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' ~/.bashrc || \
  echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
ok "CUDA PATH configured"

# ─── Step 4: nvidia-smi symlink ───────────────────────────────────────────────
info "Setting up nvidia-smi..."
if [ -f /usr/lib/wsl/lib/nvidia-smi ]; then
  sudo ln -sf /usr/lib/wsl/lib/nvidia-smi /usr/local/bin/nvidia-smi
  ok "nvidia-smi symlinked"
else
  warn "WSL2 nvidia-smi not found at /usr/lib/wsl/lib/ — check NVIDIA Windows driver"
fi

# ─── Step 5: Ollama ───────────────────────────────────────────────────────────
info "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh
ok "Ollama installed"

# ─── Step 6: Configure Ollama service ─────────────────────────────────────────
info "Configuring Ollama to listen on all interfaces..."
sudo systemctl stop ollama 2>/dev/null || true

# Write service file with OLLAMA_HOST override
sudo cp /etc/systemd/system/ollama.service /etc/systemd/system/ollama.service.bak
sudo sed -i '/\[Service\]/a Environment="OLLAMA_HOST=0.0.0.0:11434"' \
  /etc/systemd/system/ollama.service

sudo systemctl daemon-reload
sudo systemctl start ollama
sudo systemctl enable ollama
ok "Ollama service configured"

# ─── Step 7: Pull models ──────────────────────────────────────────────────────
info "Pulling LLM models (this will take a while)..."
echo "Pulling mistral:7b-instruct-q4_K_M (~4.4GB)..."
ollama pull mistral:7b-instruct-q4_K_M
echo "Pulling nomic-embed-text (~274MB)..."
ollama pull nomic-embed-text
ok "Models downloaded"

# ─── Step 8: Docker ───────────────────────────────────────────────────────────
info "Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
ok "Docker installed"

# ─── Step 9: Open WebUI ───────────────────────────────────────────────────────
info "Launching Open WebUI..."
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  --restart always \
  ghcr.io/open-webui/open-webui:main
ok "Open WebUI launched"

# ─── Step 10: ChromaDB ────────────────────────────────────────────────────────
info "Launching ChromaDB..."
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v chromadb-data:/chroma/chroma \
  --restart always \
  chromadb/chroma
ok "ChromaDB launched"

# ─── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo -e "${GREEN} Phase 1 Setup Complete!${NC}"
echo "=============================================="
echo ""
echo "Services running:"
echo "  🤖 Ollama API:    http://$(hostname -I | awk '{print $1}'):11434"
echo "  💬 Open WebUI:    http://localhost:3000"
echo "  🗄️  ChromaDB:      http://localhost:8000"
echo ""
echo "Models available:"
ollama list
echo ""
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
echo ""
warn "NOTE: Log out and back in for Docker group permissions to take effect"
warn "NOTE: In Open WebUI → Settings → Connections → set Ollama URL to:"
echo "       http://$(hostname -I | awk '{print $1}'):11434"
