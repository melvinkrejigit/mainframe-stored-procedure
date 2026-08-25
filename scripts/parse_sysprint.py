"""Extract a V-number from Zowe job output without assuming one output format."""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: parse_sysprint.py <zowe-output>")

raw = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
try:
    content = json.dumps(json.loads(raw))
except json.JSONDecodeError:
    content = raw

matches = re.findall(r"\bV([0-9]+)\b", content, re.IGNORECASE)
if not matches:
    raise SystemExit("No V-number found in Zowe SYSOUT")
versions = {f"V{number}" for number in matches}
if len(versions) != 1:
    raise SystemExit(f"Multiple versions found in Zowe SYSOUT: {', '.join(sorted(versions))}")
print(next(iter(versions)))