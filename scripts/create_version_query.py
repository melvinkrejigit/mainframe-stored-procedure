"""Create the configured version query as an FB80 text file."""
import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: create_version_query.py <application.json> <output.sql>")

application = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
query = application.get("versionCheck", {}).get("query", "").strip()
if not query:
    raise SystemExit("application.json is missing versionCheck.query")
if len(query) > 72:
    raise SystemExit("versionCheck.query must fit within 72 characters")
if not query.endswith(";"):
    raise SystemExit("versionCheck.query must end with a semicolon")

Path(sys.argv[2]).write_text(query.ljust(80) + "\n", encoding="utf-8")
print(f"Created version query at {sys.argv[2]}")