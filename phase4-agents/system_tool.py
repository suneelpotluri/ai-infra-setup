"""
System Tool — gets CPU, memory and disk from all servers via SSH
"""
import subprocess

# ── Server inventory ──────────────────────────────────────
SERVERS = {
    "pg1":     {"ip": "192.168.0.127", "user": "rockylinux"},
    "pg2":     {"ip": "192.168.0.183", "user": "rockylinux"},
    "pg3":     {"ip": "192.168.0.158", "user": "rockylinux"},
    "mongodb": {"ip": "192.168.0.120", "user": "rockylinux"},
}

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=5",
    "-o", "BatchMode=yes"  # uses SSH keys, no password prompt
]

def run_ssh(ip: str, user: str, command: str) -> str:
    """Run command on remote server via SSH"""
    try:
        result = subprocess.run(
            ["ssh"] + SSH_OPTS + [f"{user}@{ip}", command],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"SSH Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Timeout connecting to server"
    except Exception as e:
        return f"Error: {str(e)}"

def get_cpu_usage(server_name: str) -> str:
    """Get CPU usage from a server"""
    server = SERVERS.get(server_name)
    if not server:
        return f"Unknown server: {server_name}"

    cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'"
    result = run_ssh(server["ip"], server["user"], cmd)
    return f"{server_name} ({server['ip']}): CPU {result}%"

def get_memory_usage(server_name: str) -> str:
    """Get memory usage from a server"""
    server = SERVERS.get(server_name)
    if not server:
        return f"Unknown server: {server_name}"

    cmd = "free -h | grep Mem"
    result = run_ssh(server["ip"], server["user"], cmd)
    return f"{server_name} ({server['ip']}): {result}"

def get_disk_usage(server_name: str) -> str:
    """Get disk usage from a server"""
    server = SERVERS.get(server_name)
    if not server:
        return f"Unknown server: {server_name}"

    cmd = "df -h / | tail -1"
    result = run_ssh(server["ip"], server["user"], cmd)
    return f"{server_name} ({server['ip']}): {result}"

def get_all_servers_report() -> str:
    """Get CPU, memory and disk report for all servers"""
    report = []
    report.append("=" * 60)
    report.append("INFRASTRUCTURE RESOURCE REPORT")
    report.append("=" * 60)

    for name, server in SERVERS.items():
        report.append(f"\n--- {name.upper()} ({server['ip']}) ---")

        # CPU
        cmd_cpu  = "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'"
        cmd_mem  = "free -h | grep Mem | awk '{print \"Total: \"$2\" | Used: \"$3\" | Free: \"$4}'"
        cmd_disk = "df -h / | tail -1 | awk '{print \"Total: \"$2\" | Used: \"$3\" | Free: \"$4\" | Use%: \"$5}'"
        cmd_load = "uptime | awk -F'load average:' '{print $2}'"

        cpu  = run_ssh(server["ip"], server["user"], cmd_cpu)
        mem  = run_ssh(server["ip"], server["user"], cmd_mem)
        disk = run_ssh(server["ip"], server["user"], cmd_disk)
        load = run_ssh(server["ip"], server["user"], cmd_load)

        report.append(f"  CPU Usage:    {cpu}%")
        report.append(f"  Memory:       {mem}")
        report.append(f"  Disk (/):     {disk}")
        report.append(f"  Load Avg:     {load}")

    report.append("\n" + "=" * 60)
    return "\n".join(report)

# ── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print(get_all_servers_report())
