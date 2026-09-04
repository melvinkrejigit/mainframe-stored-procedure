"""Record a component's USS deployment path for a given build in the manifest."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if len(sys.argv) != 5:
    raise SystemExit("usage: update_components_manifest.py <manifest.json> <component> <buildId> <ussPath>")

manifest_path = Path(sys.argv[1])
component = sys.argv[2]
build_id = sys.argv[3]
uss_path = sys.argv[4]

manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
entry = manifest.setdefault(component, {})
deployments = entry.setdefault("deployments", {})
deployments[build_id] = {
    "ussPath": uss_path,
    "deployedAt": datetime.now(timezone.utc).isoformat(),
}
entry["latestBuildId"] = build_id
entry["latestUssPath"] = uss_path

manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"Updated {manifest_path} for component '{component}' (build {build_id})")
