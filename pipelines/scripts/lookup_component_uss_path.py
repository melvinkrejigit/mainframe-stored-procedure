"""Look up the recorded USS path for a component at a specific build ID."""
import json
import sys
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: lookup_component_uss_path.py <manifest.json> <component> <buildId>")

manifest_path = Path(sys.argv[1])
component = sys.argv[2]
build_id = sys.argv[3]

if not manifest_path.exists():
    raise SystemExit(f"Manifest not found: {manifest_path}")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
entry = manifest.get(component)
if not entry:
    raise SystemExit(f"No deployment history found for component '{component}'")

deployment = entry.get("deployments", {}).get(build_id)
if not deployment:
    raise SystemExit(f"No deployment recorded for component '{component}' at build {build_id}")

print(deployment["ussPath"])
