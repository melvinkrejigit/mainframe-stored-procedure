"""Extract one pipe-delimited V-number from SYSPRINT spool output."""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: parse_sysprint.py <zowe-output>")

raw = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
try:
    response = json.loads(raw)
except json.JSONDecodeError:
    response = None


def sysprint_text(value):
    if isinstance(value, dict):
        name = str(value.get("ddName", value.get("ddname", value.get("name", "")))).upper()
        if name == "SYSPRINT":
            return json.dumps(value)
        for item in value.values():
            result = sysprint_text(item)
            if result:
                return result
    elif isinstance(value, list):
        for item in value:
            result = sysprint_text(item)
            if result:
                return result
    return ""


content = sysprint_text(response) if response is not None else raw
if not content:
    raise SystemExit("SYSPRINT was not found in Zowe job output")
matches = re.findall(r"\|\s*(V[0-9]+)\s*\|", content, re.IGNORECASE)
if not matches:
    raise SystemExit("No pipe-delimited V-number found in SYSPRINT")
versions = {number.upper() for number in matches}
if len(versions) != 1:
    raise SystemExit(f"Multiple versions found in SYSPRINT: {', '.join(sorted(versions))}")
print(next(iter(versions)))