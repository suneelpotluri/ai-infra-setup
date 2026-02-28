# Phase 2 — Log Collection Setup

## 🔜 Status: Next Phase

## Goal
Ship logs from all infrastructure VMs to a central Loki instance on the laptop, then visualize in Grafana.

## Components
- **Loki** — Central log storage (runs on laptop WSL2)
- **Grafana** — Log visualization (runs on laptop WSL2)
- **Promtail** — Log shipping agent (runs on each VM)

## Setup Order
1. Deploy Loki + Grafana on laptop
2. Install Promtail on PostgreSQL nodes (Ubuntu)
3. Install Promtail on MongoDB VM
4. Install Promtail on Ansible VM (RHEL/Rocky)
5. Deploy Promtail DaemonSet on Kubernetes
6. Verify all logs visible in Grafana

## Before You Start — Note Your VM IPs
```
PostgreSQL Node 1:  ___________
PostgreSQL Node 2:  ___________
PostgreSQL Node 3:  ___________
MongoDB VM:         ___________
Ansible VM:         ___________
K8s Master:         ___________
K8s Worker 1:       ___________
K8s Worker 2:       ___________
Laptop WSL2 IP:     172.21.47.67  (run: hostname -I inside WSL2)
```

## Step 1 — Deploy Loki + Grafana on Laptop

```bash
cd ~/ai-infra-repo/phase2-log-collection/loki
docker compose up -d

# Verify
curl http://localhost:3100/ready
# Open Grafana: http://localhost:3001 (admin/admin123)
```

## Step 2 — Add Loki as Grafana Data Source
1. Open http://localhost:3001
2. Login: admin / admin123
3. Go to: Connections → Data Sources → Add → Loki
4. URL: http://loki:3100
5. Save & Test

## Verify Logs Are Flowing
In Grafana → Explore → Select Loki → Run:
```
{job="postgresql"}
{job="mongodb"}
{job="ansible"}
{job="kubernetes-pods"}
```
