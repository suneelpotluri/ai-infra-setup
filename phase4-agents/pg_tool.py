"""
PostgreSQL Tool — runs live SQL queries against ppg-cluster
"""
import psycopg2
from psycopg2.extras import RealDictCursor

# ── Connection config ─────────────────────────────────────
PG_CONFIG = {
    "host":     "192.168.0.127",  # pg1 - primary
    "port":     15432,             # Patroni port
    "database": "postgres",
    "user":     "postgres",
    "password": "postgres",        # update if different
    "connect_timeout": 5
}

def run_query(sql: str) -> str:
    """Run a SQL query and return results as string"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "Query returned no results"

        # Format as readable table
        result = []
        for row in rows:
            result.append(str(dict(row)))
        return "\n".join(result)

    except Exception as e:
        return f"PostgreSQL Error: {str(e)}"

# ── Pre-built queries ─────────────────────────────────────
def get_replication_status() -> str:
    return run_query("""
        SELECT client_addr, state, sent_lsn, 
               write_lsn, flush_lsn, replay_lsn,
               sync_state
        FROM pg_stat_replication;
    """)

def get_active_connections() -> str:
    return run_query("""
        SELECT datname, usename, application_name,
               client_addr, state, wait_event_type,
               wait_event, query_start::text,
               LEFT(query, 100) as query
        FROM pg_stat_activity
        WHERE state != 'idle'
        AND pid != pg_backend_pid()
        ORDER BY query_start;
    """)

def get_slow_queries() -> str:
    return run_query("""
        SELECT calls, mean_exec_time::numeric(10,2) as avg_ms,
               max_exec_time::numeric(10,2) as max_ms,
               LEFT(query, 150) as query
        FROM pg_stat_statements
        ORDER BY mean_exec_time DESC
        LIMIT 10;
    """)

def get_database_sizes() -> str:
    return run_query("""
        SELECT datname,
               pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database
        ORDER BY pg_database_size(datname) DESC;
    """)

def get_locks() -> str:
    return run_query("""
        SELECT pid, usename, pg_blocking_pids(pid) as blocked_by,
               wait_event, state,
               LEFT(query, 100) as query
        FROM pg_stat_activity
        WHERE cardinality(pg_blocking_pids(pid)) > 0;
    """)

# ── Test connection ───────────────────────────────────────
if __name__ == "__main__":
    print("Testing PostgreSQL connection...")
    print(get_replication_status())
    print("\nActive connections:")
    print(get_active_connections())
    print("\nDatabase sizes:")
    print(get_database_sizes())
