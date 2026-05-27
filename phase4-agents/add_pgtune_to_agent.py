"""
Patch script — adds pgtune_tool entries to agent.py
Run from: ~/ai-infra-setup/phase4-agents/
Usage: python3 ~/add_pgtune_to_agent.py
"""
import re

agent_file = "agent.py"

with open(agent_file, "r") as f:
    content = f.read()

# 1. Add import
if "import pgtune_tool" not in content:
    content = content.replace(
        "import re",
        "import re\nimport pgtune_tool"
    )
    print("✅ Added pgtune_tool import")
else:
    print("⏭️  pgtune_tool import already present")

# 2. Add tools to TOOLS dict — insert before the closing brace
new_tools = '''    "pg_tuning":       ("Get PGTune-style tuning recommendations for PostgreSQL",  pgtune_tool.get_tuning_recommendations),
    "pg_security":     ("Run a security hardening audit on PostgreSQL",             pgtune_tool.get_security_audit),
    "pg_full_health":  ("Get combined tuning + security audit report",              pgtune_tool.get_full_health_report),'''

if "pg_tuning" not in content:
    # Find the last tool entry and add after it
    content = content.replace(
        '    "all_servers_report": ("Get CPU, memory and disk report for ALL servers",  system_tool.get_all_servers_report),',
        '    "all_servers_report": ("Get CPU, memory and disk report for ALL servers",  system_tool.get_all_servers_report),\n' + new_tools
    )
    print("✅ Added pgtune tools to TOOLS registry")
else:
    print("⏭️  pgtune tools already present")

with open(agent_file, "w") as f:
    f.write(content)

print("✅ agent.py patched successfully")
