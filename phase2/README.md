# Phase 2 — Log Collection

## Status: ✅ Complete

## Components Deployed
- Loki 2.9.3 — Central log storage (WSL2 port 3100)
- Grafana — Visualization (WSL2 port 3001)
- Promtail — Log agents on all VMs

## Nodes Collecting Logs

| Node | IP | OS | Jobs |
|---|---|---|---|
| pg-node1 | 192.168.56.11 | CentOS 7.9 | postgresql, system |
| pg-node2 | 192.168.56.12 | CentOS 7.9 | postgresql, system |
| pg-witness | 192.168.56.13 | CentOS 7.9 | system |
| MongoDB | 192.168.0.120 | Rocky 8 | mongodb, system |
| pg1 | 192.168.0.127 | Rocky 8.10 | postgresql, system |
| pg2 | 192.168.0.183 | Rocky 8.10 | postgresql, system |
| pg3 | 192.168.0.158 | Rocky 8.10 | postgresql, system |
| k8s-control-1 | 192.168.56.31 | Rocky 9 | kubernetes-nodes |
| k8s-worker-1 | 192.168.56.41 | Rocky 9 | kubernetes-nodes |
| k8s-worker-2 | 192.168.56.42 | Rocky 9 | kubernetes-nodes |

## Key Lessons Learned
- SELinux must be set to permissive on Rocky Linux for Promtail
- Loki rate limits need to be increased for multiple nodes
- Promtail needs readline_rate limit to avoid flooding Loki
- IP conflicts can cause SSH failures (broadband extender had same IP as pg3)
- WSL2 IP (172.21.47.67) is reachable from both 192.168.56.x and 192.168.0.x networks

## Log Paths by OS
| OS | PostgreSQL Logs | System Logs |
|---|---|---|
| CentOS 7.9 | /var/lib/pgsql/14/data/log/*.log | /var/log/messages |
| Rocky 8.10 | /home/pgdata/log/*.log | /var/log/messages |
| Rocky 8 (MongoDB) | /var/log/mongo/mongod.log | /var/log/messages |

## Quick Queries in Grafana
- All PostgreSQL logs: {job="postgresql"}
- Specific cluster: {cluster="postgres-cluster"}
- MongoDB logs: {job="mongodb"}
- K8s logs: {job="kubernetes-nodes"}
- Errors only: {job="postgresql"} |= "ERROR"
