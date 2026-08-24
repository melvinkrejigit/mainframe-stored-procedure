"""Validate the initial DB2 SQL source before later deployment stages."""
import re
import sys
from pathlib import Path

SUPPORTED_STATEMENTS = {"SELECT"}


def validate_sql(path: Path) -> None:
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise ValueError("SQL file is empty")
    if "\x00" in text:
        raise ValueError("SQL file contains NUL bytes")

    without_comments = re.sub(r"--[^\r\n]*|/\*.*?\*/", " ", text, flags=re.DOTALL)
    if not without_comments.strip():
        raise ValueError("SQL file contains comments only")
    if not text.rstrip().endswith(";"):
        raise ValueError("SQL statement must end with a semicolon")

    statements = [statement.strip() for statement in without_comments.split(";") if statement.strip()]
    for statement in statements:
        match = re.match(r"([A-Za-z]+)", statement)
        if not match or match.group(1).upper() not in SUPPORTED_STATEMENTS:
            keyword = match.group(1).upper() if match else "unknown"
            raise ValueError(f"Unsupported SQL statement: {keyword}")

    normalized = " ".join(without_comments.upper().split())
    if "CURRENT TIMESTAMP" not in normalized:
        raise ValueError("Expected CURRENT TIMESTAMP expression")
    if "SYSIBM.SYSDUMMY1" not in normalized:
        raise ValueError("Expected SYSIBM.SYSDUMMY1 table")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_sql.py <sql-file>")
    try:
        validate_sql(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"SQL validation failed: {error}")
    print(f"SQL validation passed: {sys.argv[1]}")
