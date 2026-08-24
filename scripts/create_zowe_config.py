"""Create a temporary Zowe config from environment variables."""
import json
import os
import sys
from pathlib import Path

required = {name: os.environ.get(name) for name in ("MAINFRAME_HOST", "MAINFRAME_USER", "MAINFRAME_PASSWORD")}
missing = [name for name, value in required.items() if not value]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

config = {
    "$schema": "./zowe.schema.json",
    "profiles": {
        "zosmf": {
            "type": "zosmf",
            "properties": {"port": int(os.environ.get("ZOSMF_PORT", "10443"))},
            "secure": [],
        },
        "global_base": {
            "type": "base",
            "properties": {
                "host": required["MAINFRAME_HOST"],
                "user": required["MAINFRAME_USER"],
                "password": required["MAINFRAME_PASSWORD"],
                "rejectUnauthorized": os.environ.get("ZOSMF_REJECT_UNAUTHORIZED", "false").lower() == "true",
            },
            "secure": ["user", "password"],
        },
    },
    "defaults": {"zosmf": "zosmf", "base": "global_base"},
}

output = Path(sys.argv[1] if len(sys.argv) > 1 else "zowe.config.json")
output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(f"Created temporary Zowe config at {output}")
