"""
Loki Tool — fetches recent logs from Loki
"""
import requests
import time
from datetime import datetime

LOKI_URL = "http://localhost:3100"

def fetch_recent_logs(job: str, host: str = None,
                      minutes: int = 60, limit: int = 50) -> str:
    """Fetch recent logs from Loki"""
    try:
        end   = int(time.time() * 1e9)
        start = int((time.time() - minutes * 60) * 1e9)

        if job == "postgresql":
            query = '{job="postgresql", cluster="ppg-cluster"}'
        elif host:
            query = f'{{job="{job}", host="{host}"}}'
        else:
            query = f'{{job="{job}"}}'

        resp = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query":     query,
                "start":     start,
                "end":       end,
                "limit":     limit,
                "direction": "backward"
            }
        )

        if resp.status_code != 200:
            return f"Loki error: {resp.text}"

        results = resp.json().get("data", {}).get("result", [])
        if not results:
            return f"No logs found for job={job}"

        logs = []
        for stream in results:
            labels     = stream.get("stream", {})
            host_label = labels.get("host", "unknown")
            for ts, line in stream.get("values", []):
                dt = datetime.fromtimestamp(int(ts) / 1e9)
                logs.append(f"[{dt.strftime('%H:%M:%S')} | {host_label}] {line}")

        return "\n".join(logs[:limit])

    except Exception as e:
        return f"Loki Error: {str(e)}"

def fetch_errors(job: str, minutes: int = 60) -> str:
    """Fetch error logs only"""
    try:
        end   = int(time.time() * 1e9)
        start = int((time.time() - minutes * 60) * 1e9)

        if job == "postgresql":
            query = '{job="postgresql", cluster="ppg-cluster"} |~ "(?i)error|fatal|panic"'
        else:
            query = f'{{job="{job}"}} |~ "(?i)error|fatal"'

        resp = requests.get(
            f"{LOKI_URL}/loki/api/v1/query_range",
            params={
                "query":     query,
                "start":     start,
                "end":       end,
                "limit":     50,
                "direction": "backward"
            }
        )

        if resp.status_code != 200:
            return f"Loki error: {resp.text}"

        results = resp.json().get("data", {}).get("result", [])
        if not results:
            return f"No errors found in {job} logs in last {minutes} minutes ✅"

        logs = []
        for stream in results:
            labels     = stream.get("stream", {})
            host_label = labels.get("host", "unknown")
            for ts, line in stream.get("values", []):
                dt = datetime.fromtimestamp(int(ts) / 1e9)
                logs.append(f"[{dt.strftime('%H:%M:%S')} | {host_label}] {line}")

        return f"Found {len(logs)} errors:\n" + "\n".join(logs[:20])

    except Exception as e:
        return f"Loki Error: {str(e)}"

# ── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Loki tool...")
    print("\nRecent PostgreSQL logs:")
    print(fetch_recent_logs("postgresql", minutes=30, limit=5))
    print("\nRecent MongoDB logs:")
    print(fetch_recent_logs("mongodb", minutes=30, limit=5))
    print("\nChecking PostgreSQL errors:")
    print(fetch_errors("postgresql", minutes=60))
    print("\nChecking MongoDB errors:")
    print(fetch_errors("mongodb", minutes=60))
