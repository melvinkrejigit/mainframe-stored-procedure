"""Extract one value between pipe characters from SYSPRINT text."""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: parse_sysprint_value.py <sysprint-file>")

content = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
matches = [
    value.strip()
    for value in re.findall(r"\|([^|]+)\|", content)
    if value.strip()
]
if not matches:
    raise SystemExit("No pipe-delimited value found in SYSPRINT")
values = set(matches)
if len(values) != 1:
    raise SystemExit(f"Multiple pipe-delimited values found: {', '.join(sorted(values))}")
print(next(iter(values)))
