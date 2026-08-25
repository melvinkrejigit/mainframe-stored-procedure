"""Extract the job ID from a Zowe JSON or text response."""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: extract_job_id.py <zowe-submit-response>")

raw = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
try:
    response = json.loads(raw)
except json.JSONDecodeError:
    response = raw


def find_job_id(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {"jobid", "job-id", "job_id"} and item:
                return str(item)
            result = find_job_id(item)
            if result:
                return result
    elif isinstance(value, list):
        for item in value:
            result = find_job_id(item)
            if result:
                return result
    return None

job_id = find_job_id(response)
if not job_id:
    match = re.search(r"\b(JOB[0-9A-Z]+)\b", raw, re.IGNORECASE)
    job_id = match.group(1) if match else None
if not job_id:
    raise SystemExit("No job ID found in Zowe submit response")
print(job_id)
