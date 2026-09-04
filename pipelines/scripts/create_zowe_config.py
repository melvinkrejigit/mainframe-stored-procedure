"""Create a temporary Zowe config from application.json and a secret env var."""
import json
import os
import sys
from pathlib import Path

if len(sys.argv) < 2:
    raise SystemExit("usage: create_zowe_config.py <application.json> [output.json]")

application = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
settings = application.get("zowe", {})
password_env = settings.get("passwordEnv", "MAINFRAME_PASSWORD")
password = os.environ.get(password_env)
if not password:
    raise SystemExit(f"Missing secret environment variable: {password_env}")
for field in ("host", "port", "user"):
    if not settings.get(field):
        raise SystemExit(f"application.json is missing zowe.{field}")

config = {
    "$schema": "./zowe.schema.json",
    "profiles": {
        "zosmf": {
            "type": "zosmf",
            "properties": {"port": int(settings["port"])},
            "secure": [],
        },
        "global_base": {
            "type": "base",
            "properties": {
                "host": settings["host"],
                "user": settings["user"],
                "password": password,
                "rejectUnauthorized": bool(settings.get("rejectUnauthorized", True)),
            },
            "secure": ["user", "password"],
        },
    },
    "defaults": {"zosmf": "zosmf", "base": "global_base"},
}

output = Path(sys.argv[2] if len(sys.argv) > 2 else "zowe.config.json")
output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(f"Created temporary Zowe config at {output}")
