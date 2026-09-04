"""Render an uploaded USS SQL path into the reusable DSNTEP2 JCL."""
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: render_sql_jcl.py <template.jcl> <uss-sql-path> <output.jcl>")

template = Path(sys.argv[1]).read_text(encoding="utf-8")
uss_path = sys.argv[2]
placeholder = "__SQL_USS_PATH__"
if template.count(placeholder) != 1:
    raise SystemExit("JCL template must contain exactly one __SQL_USS_PATH__ placeholder")
if not uss_path.startswith("/") or "'" in uss_path:
    raise SystemExit("USS SQL path must be an absolute path without single quotes")

Path(sys.argv[3]).write_text(template.replace(placeholder, uss_path), encoding="utf-8")
print(f"Rendered SQL execution JCL at {sys.argv[3]}")
