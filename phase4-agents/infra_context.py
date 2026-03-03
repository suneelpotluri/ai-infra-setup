"""
Dynamic Infrastructure Context
Queries live systems to get current topology
"""
import pg_tool
import mongo_tool

def get_live_context() -> str:
    """Build infrastructure context from live data"""
    context_parts = []

    # ── PostgreSQL Live Topology ──────────────────────────
    try:
        # Get replication status to find who is primary
        repl = pg_tool.get_replication_status()

        # Get patroni leader info
        import psycopg2
        conn = psycopg2.connect(**pg_tool.PG_CONFIG)
        cur  = conn.cursor()

        # Who am I?
        cur.execute("SELECT inet_server_addr(), inet_server_port();")
        server_ip, server_port = cur.fetchone()

        # Am I the primary?
        cur.execute("SELECT pg_is_in_recovery();")
        is_replica = cur.fetchone()[0]

        # Get all replication connections (replicas)
        cur.execute("""
            SELECT client_addr, application_name, state, sync_state
            FROM pg_stat_replication;
        """)
        replicas = cur.fetchall()

        cur.close()
        conn.close()

        role = "REPLICA" if is_replica else "PRIMARY/LEADER"
        pg_context = f"""
PostgreSQL ppg-cluster (Patroni HA) - LIVE STATUS:
- Connected to: {server_ip}:{server_port} → Role: {role}
- Replicas streaming:"""

        if replicas:
            for r in replicas:
                pg_context += f"\n  * {r[1]} ({r[0]}) → state={r[2]}"
        else:
            pg_context += "\n  * No replicas connected"

        context_parts.append(pg_context)

    except Exception as e:
        context_parts.append(f"PostgreSQL topology: Could not fetch ({e})")

    # ── MongoDB Live Status ───────────────────────────────
    try:
        from pymongo import MongoClient
        client = MongoClient(
            host=mongo_tool.MONGO_CONFIG["host"],
            port=mongo_tool.MONGO_CONFIG["port"],
            username=mongo_tool.MONGO_CONFIG.get("username"),
            password=mongo_tool.MONGO_CONFIG.get("password"),
            authSource=mongo_tool.MONGO_CONFIG.get("authSource", "admin"),
            serverSelectionTimeoutMS=3000
        )
        info = client.server_info()
        client.close()

        mongo_context = f"""
MongoDB - LIVE STATUS:
- Host: {mongo_tool.MONGO_CONFIG['host']}:27017
- Version: {info.get('version')}
- Type: Standalone"""

        context_parts.append(mongo_context)

    except Exception as e:
        context_parts.append(f"MongoDB topology: Could not fetch ({e})")

    # ── Static context (doesn't change) ──────────────────
    static_context = """
Static Infrastructure:
- postgres-cluster (CentOS 7.9):
  * pg-node1 (192.168.56.11) = PRIMARY
  * pg-node2 (192.168.56.12) = REPLICA
- Kubernetes (Rocky 9):
  * k8s-control-1 (192.168.56.31)
  * k8s-worker-1  (192.168.56.41)
  * k8s-worker-2  (192.168.56.42)
- All logs available in Loki
- Patroni manages automatic failover for ppg-cluster"""

    context_parts.append(static_context)

    return "\n".join(context_parts)

# ── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching live infrastructure context...")
    print(get_live_context())
