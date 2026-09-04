"""Render the configurable version query into the reusable JCL template."""
import json
import sys
from pathlib import Path

if len(sys.argv) not in (4, 5, 6):
    raise SystemExit(
        "usage: render_version_jcl.py <application.json> <template.jcl> <output.jcl> [query-key] [section]"
    )

application = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
query_key = sys.argv[4] if len(sys.argv) == 5 else "query"
section = sys.argv[5] if len(sys.argv) == 6 else "versionCheck"
query = application.get(section, {}).get(query_key, "").strip()
if not query:
    raise SystemExit(f"application.json is missing {section}.{query_key}")
if "\r" in query or "\n" in query:
    raise SystemExit("versionCheck.query must be a single line")
if len(query) > 72:
    raise SystemExit("versionCheck.query must fit within 72 characters")
if not query.endswith(";"):
    raise SystemExit("versionCheck.query must end with a semicolon")

template = Path(sys.argv[2]).read_text(encoding="utf-8")
placeholder = "__VERSION_QUERY__"
if template.count(placeholder) != 1:
    raise SystemExit("JCL template must contain exactly one __VERSION_QUERY__ placeholder")

Path(sys.argv[3]).write_text(
    template.replace(placeholder, query), encoding="utf-8"
)
print(f"Rendered version-check JCL at {sys.argv[3]}")