# Phase 1 — Central AI Server Setup

## ✅ Status: Complete

## What Was Set Up

| Component | Version | Status |
|---|---|---|
| WSL2 Ubuntu 22.04 | 22.04.5 LTS | ✅ Running on F: drive |
| NVIDIA Driver | 566.07 | ✅ GPU passthrough working |
| CUDA Toolkit | 12.7 | ✅ Installed |
| nvidia-smi (WSL2) | 565.65 | ✅ Symlinked from /usr/lib/wsl/lib/ |
| Ollama | Latest | ✅ Running as systemd service |
| Mistral 7B Q4_K_M | 4.4GB | ✅ Downloaded |
| nomic-embed-text | 274MB | ✅ Downloaded |
| Docker CE | Latest | ✅ Installed |
| Open WebUI | v0.8.5 | ✅ Running on port 3000 |

## Setup Steps

### 1. WSL2 Installation (PowerShell as Admin)
```powershell
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
```

### 2. Move WSL2 to F: Drive (PowerShell as Admin)
```powershell
wsl --terminate Ubuntu-22.04
wsl --export Ubuntu-22.04 "F:\WSL\ubuntu2204.tar"
wsl --unregister Ubuntu-22.04
mkdir F:\WSL\Ubuntu2204
wsl --import Ubuntu-22.04 "F:\WSL\Ubuntu2204" "F:\WSL\ubuntu2204.tar"
wsl -d Ubuntu-22.04 -u root bash -c "echo -e '[user]\ndefault=sunilp' >> /etc/wsl.conf"
wsl --terminate Ubuntu-22.04
```

### 3. CUDA Setup (WSL2 Ubuntu)
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get install -y cuda-toolkit-12-3

# Add to PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Symlink nvidia-smi
sudo ln -sf /usr/lib/wsl/lib/nvidia-smi /usr/local/bin/nvidia-smi
```

### 4. Ollama Installation
```bash
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull mistral:7b-instruct-q4_K_M
ollama pull nomic-embed-text
```

### 5. Configure Ollama to Listen on All Interfaces
```bash
sudo systemctl stop ollama
sudo nano /etc/systemd/system/ollama.service
# Add under [Service]: Environment="OLLAMA_HOST=0.0.0.0:11434"
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### 6. Docker Installation
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

### 7. Open WebUI Launch
```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

## Key Notes

- WSL2 uses Windows NVIDIA driver via passthrough — do NOT install Linux nvidia drivers inside WSL2
- `nvidia-smi` lives at `/usr/lib/wsl/lib/nvidia-smi` in WSL2, not standard path
- Ollama runs as a systemd service under `ollama` user
- RTX 3060 has 6GB VRAM — use quantized models (Q4_K_M) for best performance
- Mistral 7B Q4_K_M fits fully in 6GB VRAM = maximum GPU speed
- Open WebUI connects to Ollama via WSL2 IP (172.21.47.67:11434), not localhost

## Verify Everything is Working
```bash
nvidia-smi                          # GPU visible
ollama list                         # Models downloaded
curl http://$(hostname -I | awk '{print $1}'):11434  # Ollama API responding
docker ps                           # Open WebUI container running
```

Then open http://localhost:3000 in Windows browser.
