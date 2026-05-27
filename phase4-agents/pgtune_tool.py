"""
PostgreSQL Tuning & Hardening Tool
Fetches live config from PostgreSQL servers, compares against PGTune-style
best practices, and returns actionable recommendations for the AI agent.

Tools registered:
  pg_tuning      — PGTune-style performance tuning recommendations
  pg_security    — Security hardening audit (SSL, auth, logging, privileges)
  pg_full_health — Combined tuning + security report
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess

# ── Connection config ─────────────────────────────────────
PG_SERVERS = {
    "pg-node1": {"host": "192.168.56.11", "port": 5432, "user": "postgres", "password": "postgres", "database": "postgres"},
    "pg-node2": {"host": "192.168.56.12", "port": 5432, "user": "postgres", "password": "postgres", "database": "postgres"},
}


# ── Helpers ───────────────────────────────────────────────
def format_size(bytes_val: int) -> str:
    """Format bytes to human readable."""
    if bytes_val >= 1024**3:
        return f"{bytes_val / 1024**3:.1f}GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / 1024**2:.0f}MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.0f}kB"
    return f"{bytes_val}B"


def run_query(config: dict, sql: str) -> list:
    """Run a SQL query and return results as list of dicts."""
    try:
        conn = psycopg2.connect(**config, connect_timeout=5)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]


def get_hardware_via_ssh(host: str) -> tuple:
    """Get RAM (bytes) and CPU count via SSH."""
    try:
        mem_result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             "-o", "BatchMode=yes", f"vagrant@{host}",
             "free -b | grep Mem | awk '{print $2}'"],
            capture_output=True, text=True, timeout=10
        )
        total_ram = int(mem_result.stdout.strip()) if mem_result.returncode == 0 else 4 * 1024**3

        cpu_result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             "-o", "BatchMode=yes", f"vagrant@{host}", "nproc"],
            capture_output=True, text=True, timeout=10
        )
        cpu_count = int(cpu_result.stdout.strip()) if cpu_result.returncode == 0 else 2
    except Exception:
        total_ram = 4 * 1024**3
        cpu_count = 2

    return total_ram, cpu_count


# ── PGTune Recommendations Engine ─────────────────────────
def calculate_pgtune_settings(total_ram_bytes: int, cpu_count: int,
                               db_type: str = "mixed",
                               max_connections: int = 100,
                               storage_type: str = "ssd") -> dict:
    """
    Calculate optimal PostgreSQL settings based on hardware.
    DB types: web, oltp, dw (data warehouse), mixed, desktop
    """
    ram = total_ram_bytes
    settings = {}

    # shared_buffers: 25% of RAM, max 8GB on Linux
    shared_buffers = min(int(ram * 0.25), 8 * 1024**3)
    settings["shared_buffers"] = shared_buffers

    # effective_cache_size: 75% of total RAM
    settings["effective_cache_size"] = int(ram * 0.75)

    # maintenance_work_mem: 5% of RAM, max 2GB
    settings["maintenance_work_mem"] = min(int(ram * 0.05), 2 * 1024**3)

    # work_mem: depends on workload type
    divisor = {"web": 4, "oltp": 3, "dw": 1.5, "mixed": 3, "desktop": 6}
    work_mem = int((ram - shared_buffers) / (max_connections * divisor.get(db_type, 3)))
    settings["work_mem"] = max(work_mem, 4 * 1024**2)  # minimum 4MB

    # wal_buffers: 3% of shared_buffers, 32kB-64MB range
    wal_buffers = int(shared_buffers * 0.03)
    settings["wal_buffers"] = max(32 * 1024, min(wal_buffers, 64 * 1024**2))

    # Checkpoint & WAL
    settings["checkpoint_completion_target"] = 0.9
    settings["max_wal_size"] = "4GB" if db_type in ("dw", "oltp") else "2GB"
    settings["min_wal_size"] = "1GB"

    # Storage tuning
    if storage_type == "ssd":
        settings["random_page_cost"] = 1.1
        settings["effective_io_concurrency"] = 200
    else:
        settings["random_page_cost"] = 4.0
        settings["effective_io_concurrency"] = 2

    # Parallelism
    settings["max_worker_processes"] = cpu_count
    settings["max_parallel_workers_per_gather"] = max(1, cpu_count // 2)
    settings["max_parallel_workers"] = cpu_count
    settings["max_parallel_maintenance_workers"] = max(1, cpu_count // 2)

    # Huge pages
    settings["huge_pages"] = "try" if ram >= 32 * 1024**3 else "off"

    return settings


# ── Security Hardening Checks ─────────────────────────────
def check_security_hardening(config: dict) -> list:
    """Check PostgreSQL security configuration and return findings."""
    findings = []

    # Simple param checks: (query, expected_value, severity, finding_message)
    simple_checks = [
        ("SHOW ssl;", "on", "CRITICAL", "SSL is disabled — all connections are unencrypted. Enable SSL for encrypted connections."),
        ("SHOW password_encryption;", "scram-sha-256", "HIGH", "Password encryption should be scram-sha-256 instead of md5 for stronger security."),
        ("SHOW log_connections;", "on", "MEDIUM", "Connection logging is disabled — cannot audit who connects to the database."),
        ("SHOW log_disconnections;", "on", "MEDIUM", "Disconnection logging is disabled — cannot track session duration."),
    ]

    for query, expected, severity, message in simple_checks:
        rows = run_query(config, query)
        if rows and "error" not in rows[0]:
            current = list(rows[0].values())[0]
            if str(current).lower() != str(expected).lower():
                findings.append({
                    "param": query.replace("SHOW ", "").replace(";", ""),
                    "current": current, "recommended": expected,
                    "severity": severity, "finding": message
                })

    # log_statement should be at least 'ddl'
    rows = run_query(config, "SHOW log_statement;")
    if rows and "error" not in rows[0]:
        val = list(rows[0].values())[0]
        if val == "none":
            findings.append({
                "param": "log_statement", "current": val, "recommended": "ddl",
                "severity": "MEDIUM", "finding": "DDL statements are not being logged. Set to 'ddl' to audit schema changes."
            })

    # log_min_duration_statement
    rows = run_query(config, "SHOW log_min_duration_statement;")
    if rows and "error" not in rows[0]:
        val = str(list(rows[0].values())[0])
        if val == "-1" or val.startswith("-"):
            findings.append({
                "param": "log_min_duration_statement", "current": val, "recommended": "1000",
                "severity": "MEDIUM", "finding": "Slow query logging is disabled. Set to 1000ms to capture queries taking over 1 second."
            })

    # log_line_prefix should include user and database
    rows = run_query(config, "SHOW log_line_prefix;")
    if rows and "error" not in rows[0]:
        val = str(list(rows[0].values())[0])
        if "%u" not in val or "%d" not in val:
            findings.append({
                "param": "log_line_prefix", "current": val,
                "recommended": "'%t [%p] %u@%d '",
                "severity": "MEDIUM", "finding": "Log prefix missing user (%u) and/or database (%d). Add them for proper audit trails."
            })

    # pg_stat_statements loaded?
    rows = run_query(config, "SHOW shared_preload_libraries;")
    if rows and "error" not in rows[0]:
        val = str(list(rows[0].values())[0])
        if "pg_stat_statements" not in val:
            findings.append({
                "param": "shared_preload_libraries", "current": val or "(empty)",
                "recommended": "pg_stat_statements",
                "severity": "MEDIUM", "finding": "pg_stat_statements not loaded. Cannot track query performance. Add it and restart PostgreSQL."
            })

    # pg_hba.conf trust entries for remote hosts
    hba_rows = run_query(config, """
        SELECT type, database, user_name, address, auth_method
        FROM pg_hba_file_rules
        WHERE auth_method = 'trust' AND type = 'host'
        ORDER BY line_number;
    """)
    if hba_rows and "error" not in hba_rows[0]:
        for rule in hba_rows:
            findings.append({
                "param": "pg_hba.conf",
                "current": f"{rule.get('type')} {rule.get('database')} {rule.get('user_name')} {rule.get('address')} trust",
                "recommended": "scram-sha-256",
                "severity": "CRITICAL",
                "finding": f"TRUST authentication allows passwordless remote access for user '{rule.get('user_name')}' from {rule.get('address')}. Change to scram-sha-256."
            })

    # Superuser count
    su_rows = run_query(config, "SELECT usename FROM pg_user WHERE usesuper = true;")
    if su_rows and "error" not in su_rows[0]:
        superusers = [r.get("usename", "") for r in su_rows]
        if len(superusers) > 1:
            findings.append({
                "param": "superuser_count", "current": ", ".join(superusers),
                "recommended": "Only 'postgres' should be superuser",
                "severity": "HIGH",
                "finding": f"Multiple superusers found ({len(superusers)}): {', '.join(superusers)}. Reduce to minimum needed."
            })

    # Public schema connect privilege
    pub_rows = run_query(config, """
        SELECT datname FROM pg_database
        WHERE datname NOT IN ('template0', 'template1')
        AND has_database_privilege('public', datname, 'CONNECT');
    """)
    if pub_rows and "error" not in pub_rows[0]:
        dbs = [r.get("datname", "") for r in pub_rows]
        if dbs:
            findings.append({
                "param": "public_connect_privilege",
                "current": f"PUBLIC can connect to: {', '.join(dbs)}",
                "recommended": "REVOKE CONNECT ON DATABASE <db> FROM PUBLIC;",
                "severity": "MEDIUM",
                "finding": f"The PUBLIC role can connect to {len(dbs)} databases. Revoke unnecessary access."
            })

    return findings


# ── Tool Functions (called by agent) ──────────────────────

def get_tuning_recommendations(server_name: str = "pg-node1") -> str:
    """Get PGTune-style tuning recommendations for a PostgreSQL server."""
    config = PG_SERVERS.get(server_name)
    if not config:
        return f"Unknown server: {server_name}. Available: {', '.join(PG_SERVERS.keys())}"

    try:
        # Fetch current settings
        hw_info = run_query(config, """
            SELECT
                (SELECT setting FROM pg_settings WHERE name = 'shared_buffers') as shared_buffers,
                (SELECT setting FROM pg_settings WHERE name = 'effective_cache_size') as effective_cache_size,
                (SELECT setting FROM pg_settings WHERE name = 'work_mem') as work_mem,
                (SELECT setting FROM pg_settings WHERE name = 'maintenance_work_mem') as maintenance_work_mem,
                (SELECT setting FROM pg_settings WHERE name = 'wal_buffers') as wal_buffers,
                (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections,
                (SELECT setting FROM pg_settings WHERE name = 'checkpoint_completion_target') as checkpoint_completion_target,
                (SELECT setting FROM pg_settings WHERE name = 'max_wal_size') as max_wal_size,
                (SELECT setting FROM pg_settings WHERE name = 'random_page_cost') as random_page_cost,
                (SELECT setting FROM pg_settings WHERE name = 'effective_io_concurrency') as effective_io_concurrency,
                (SELECT setting FROM pg_settings WHERE name = 'max_worker_processes') as max_worker_processes,
                (SELECT setting FROM pg_settings WHERE name = 'max_parallel_workers_per_gather') as max_parallel_workers_per_gather,
                (SELECT setting FROM pg_settings WHERE name = 'max_parallel_workers') as max_parallel_workers,
                (SELECT setting FROM pg_settings WHERE name = 'huge_pages') as huge_pages,
                (SELECT setting FROM pg_settings WHERE name = 'server_version') as server_version;
        """)

        if not hw_info or "error" in hw_info[0]:
            return f"Error fetching config: {hw_info}"

        current = hw_info[0]
        max_conns = int(current.get("max_connections", 100))

        # Get hardware info
        total_ram, cpu_count = get_hardware_via_ssh(config["host"])

        # Calculate recommended settings
        recommended = calculate_pgtune_settings(
            total_ram_bytes=total_ram, cpu_count=cpu_count,
            db_type="mixed", max_connections=max_conns, storage_type="ssd"
        )

        # Build comparison report with explicit directions
        report = []
        report.append(f"{'='*70}")
        report.append(f"PGTUNE RECOMMENDATIONS — {server_name} ({config['host']})")
        report.append(f"{'='*70}")
        report.append(f"Hardware detected: {format_size(total_ram)} RAM, {cpu_count} CPUs, SSD storage")
        report.append(f"PostgreSQL version: {current.get('server_version', 'unknown')}")
        report.append(f"Max connections: {max_conns}")
        report.append(f"Workload type: Mixed (OLTP + Reporting)")
        report.append(f"{'-'*70}")
        report.append(f"{'Parameter':<42} {'Current':<12} {'Recommended':<12} {'Status'}")
        report.append(f"{'-'*70}")

        # Memory params (stored in 8kB blocks in pg_settings)
        memory_params = {
            "shared_buffers":       8192,
            "effective_cache_size": 8192,
            "work_mem":            1024,
            "maintenance_work_mem": 1024,
            "wal_buffers":         8192,
        }

        changes_needed = []

        for param, block_size in memory_params.items():
            if param in recommended:
                current_bytes = int(current.get(param, 0)) * block_size
                rec_bytes = recommended[param]
                cur_fmt = format_size(current_bytes)
                rec_fmt = format_size(rec_bytes)
                diff_pct = abs(current_bytes - rec_bytes) / max(rec_bytes, 1)

                if diff_pct > 0.2:
                    if current_bytes < rec_bytes:
                        status = f"⚠️  TOO LOW — INCREASE from {cur_fmt} to {rec_fmt}"
                        changes_needed.append(f"{param} = '{rec_fmt}'  # INCREASE from {cur_fmt}")
                    else:
                        status = f"⚠️  TOO HIGH — DECREASE from {cur_fmt} to {rec_fmt}"
                        changes_needed.append(f"{param} = '{rec_fmt}'  # DECREASE from {cur_fmt}")
                else:
                    status = "✅ OK"

                report.append(f"{param:<42} {cur_fmt:<12} {rec_fmt:<12} {status}")

        # Numeric params
        numeric_params = [
            "checkpoint_completion_target", "random_page_cost",
            "effective_io_concurrency", "max_worker_processes",
            "max_parallel_workers_per_gather", "max_parallel_workers",
            "max_parallel_maintenance_workers",
        ]

        for param in numeric_params:
            if param in recommended:
                rec_val = recommended[param]
                cur_val = current.get(param, "N/A")
                try:
                    cur_num = float(cur_val)
                    rec_num = float(rec_val)
                    diff_pct = abs(cur_num - rec_num) / max(rec_num, 0.01)

                    if diff_pct > 0.2:
                        if cur_num < rec_num:
                            status = f"⚠️  TOO LOW — INCREASE from {cur_val} to {rec_val}"
                            changes_needed.append(f"{param} = {rec_val}  # INCREASE from {cur_val}")
                        else:
                            status = f"⚠️  TOO HIGH — DECREASE from {cur_val} to {rec_val}"
                            changes_needed.append(f"{param} = {rec_val}  # DECREASE from {cur_val}")
                    else:
                        status = "✅ OK"
                except (ValueError, TypeError):
                    status = "⚠️  Cannot compare"

                report.append(f"{param:<42} {str(cur_val):<12} {str(rec_val):<12} {status}")

        # String params
        for param in ["huge_pages", "max_wal_size", "min_wal_size"]:
            if param in recommended:
                rec_val = str(recommended[param])
                cur_val = str(current.get(param, "N/A"))
                if cur_val.lower() != rec_val.lower():
                    status = f"⚠️  CHANGE from '{cur_val}' to '{rec_val}'"
                    changes_needed.append(f"{param} = '{rec_val}'  # CHANGE from '{cur_val}'")
                else:
                    status = "✅ OK"
                report.append(f"{param:<42} {cur_val:<12} {rec_val:<12} {status}")

        report.append(f"{'-'*70}")

        if changes_needed:
            report.append(f"\nSUMMARY: {len(changes_needed)} parameters need adjustment.\n")
            report.append("ADD THESE TO postgresql.conf:")
            for change in changes_needed:
                report.append(f"  {change}")
            report.append(f"\nAPPLY CHANGES:")
            report.append(f"  SELECT pg_reload_conf();")
            report.append(f"  NOTE: shared_buffers and shared_preload_libraries require a full restart.")
        else:
            report.append("\nSUMMARY: All settings are within recommended range. No changes needed.")

        report.append(f"{'='*70}")
        return "\n".join(report)

    except Exception as e:
        return f"Error: {str(e)}"


def get_security_audit(server_name: str = "pg-node1") -> str:
    """Run a security hardening audit on a PostgreSQL server."""
    config = PG_SERVERS.get(server_name)
    if not config:
        return f"Unknown server: {server_name}. Available: {', '.join(PG_SERVERS.keys())}"

    try:
        findings = check_security_hardening(config)

        report = []
        report.append(f"{'='*70}")
        report.append(f"SECURITY HARDENING AUDIT — {server_name} ({config['host']})")
        report.append(f"{'='*70}")

        if not findings:
            report.append("RESULT: No security issues found. All checks passed.")
            return "\n".join(report)

        critical = [f for f in findings if f["severity"] == "CRITICAL"]
        high = [f for f in findings if f["severity"] == "HIGH"]
        medium = [f for f in findings if f["severity"] == "MEDIUM"]
        low = [f for f in findings if f["severity"] == "LOW"]

        report.append(f"RESULT: {len(findings)} security issues found.")
        report.append(f"  CRITICAL: {len(critical)}  |  HIGH: {len(high)}  |  MEDIUM: {len(medium)}  |  LOW: {len(low)}")
        report.append(f"{'-'*70}")

        for severity, label, items in [
            ("CRITICAL", "CRITICAL ISSUES (fix immediately)", critical),
            ("HIGH", "HIGH SEVERITY ISSUES", high),
            ("MEDIUM", "MEDIUM SEVERITY ISSUES", medium),
            ("LOW", "LOW SEVERITY ISSUES", low),
        ]:
            if items:
                report.append(f"\n--- {label} ---")
                for i, f in enumerate(items, 1):
                    report.append(f"\n  Issue {i}: {f['finding']}")
                    report.append(f"    Parameter:   {f['param']}")
                    report.append(f"    Current:     {f['current']}")
                    report.append(f"    Recommended: {f['recommended']}")

        # Remediation commands
        report.append(f"\n{'-'*70}")
        report.append("REMEDIATION COMMANDS:")
        for f in findings:
            param = f["param"]
            rec = f["recommended"]
            if param == "pg_hba.conf":
                report.append(f"  -- Edit pg_hba.conf: replace 'trust' with '{rec}' for remote entries")
                report.append(f"  -- Then run: SELECT pg_reload_conf();")
            elif param in ("superuser_count", "public_connect_privilege"):
                report.append(f"  -- {f['finding']}")
                if "REVOKE" in rec:
                    report.append(f"  {rec}")
            elif param == "shared_preload_libraries":
                report.append(f"  -- Add to postgresql.conf: shared_preload_libraries = '{rec}'")
                report.append(f"  -- Requires PostgreSQL restart")
            else:
                report.append(f"  ALTER SYSTEM SET {param} = '{rec}';")

        report.append(f"\n  -- Apply non-restart changes: SELECT pg_reload_conf();")
        report.append(f"  -- Restart-required changes: sudo systemctl restart postgresql-14")
        report.append(f"{'='*70}")
        return "\n".join(report)

    except Exception as e:
        return f"Error: {str(e)}"


def get_full_health_report(server_name: str = "pg-node1") -> str:
    """Get combined tuning + security audit report."""
    tuning = get_tuning_recommendations(server_name)
    security = get_security_audit(server_name)
    return f"{tuning}\n\n{security}"


# ── Standalone test ───────────────────────────────────────
if __name__ == "__main__":
    print("Testing PGTune recommendations on pg-node1...\n")
    print(get_tuning_recommendations("pg-node1"))
    print("\n")
    print("Testing Security Audit on pg-node1...\n")
    print(get_security_audit("pg-node1"))
