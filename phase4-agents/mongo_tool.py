"""
MongoDB Tool — runs live commands against MongoDB
"""
from pymongo import MongoClient
import json

# ── Connection config ─────────────────────────────────────
MONGO_CONFIG = {
    "host":             "192.168.0.120",
    "username":         "root",
    "password":         "Admin@123",
    "authSource":       "admin",
    "port":             27017,
    "serverSelectionTimeoutMS": 5000
}

def get_client():
    return MongoClient(**MONGO_CONFIG)

def run_command(db_name: str, command: dict) -> str:
    """Run a MongoDB command and return results as string"""
    try:
        client = get_client()
        db     = client[db_name]
        result = db.command(command)
        client.close()
        # Remove ok field for cleaner output
        result.pop("ok", None)
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return f"MongoDB Error: {str(e)}"

# ── Pre-built commands ────────────────────────────────────
def get_server_status() -> str:
    """Get MongoDB server status"""
    try:
        client = get_client()
        db     = client["admin"]
        status = db.command("serverStatus")
        client.close()

        # Extract key metrics only
        summary = {
            "host":          status.get("host"),
            "version":       status.get("version"),
            "uptime_hours":  round(status.get("uptime", 0) / 3600, 1),
            "connections":   status.get("connections"),
            "opcounters":    status.get("opcounters"),
            "memory_MB":     status.get("mem"),
        }
        return json.dumps(summary, default=str, indent=2)
    except Exception as e:
        return f"MongoDB Error: {str(e)}"

def get_databases() -> str:
    """List all databases with sizes"""
    try:
        client = get_client()
        dbs    = client.list_database_names()
        result = []
        for db_name in dbs:
            db   = client[db_name]
            stats = db.command("dbStats")
            result.append({
                "database":   db_name,
                "size":       f"{round(stats.get('dataSize', 0) / 1024, 1)} KB",
                "collections": stats.get("collections", 0),
                "objects":    stats.get("objects", 0)
            })
        client.close()
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return f"MongoDB Error: {str(e)}"

def get_slow_operations() -> str:
    """Get current slow operations"""
    try:
        client  = get_client()
        db      = client["admin"]
        current = db.command("currentOp", {"secs_running": {"$gte": 1}})
        ops     = current.get("inprog", [])
        client.close()

        if not ops:
            return "No slow operations currently running"

        result = []
        for op in ops:
            result.append({
                "opid":        op.get("opid"),
                "op":          op.get("op"),
                "ns":          op.get("ns"),
                "secs_running": op.get("secs_running"),
                "desc":        op.get("desc")
            })
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return f"MongoDB Error: {str(e)}"

def get_replica_status() -> str:
    """Get replica set status"""
    try:
        client = get_client()
        db     = client["admin"]
        status = db.command("replSetGetStatus")
        client.close()
        members = []
        for m in status.get("members", []):
            members.append({
                "name":   m.get("name"),
                "state":  m.get("stateStr"),
                "health": m.get("health"),
                "lag_seconds": m.get("optimeDate")
            })
        return json.dumps(members, default=str, indent=2)
    except Exception as e:
        return f"Not a replica set or error: {str(e)}"

# ── Test connection ───────────────────────────────────────
if __name__ == "__main__":
    print("Testing MongoDB connection...")
    print("\nServer Status:")
    print(get_server_status())
    print("\nDatabases:")
    print(get_databases())
    print("\nSlow Operations:")
    print(get_slow_operations())
