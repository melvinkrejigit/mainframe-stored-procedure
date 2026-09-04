"""Validate every DB2 SQL source file before later deployment stages."""
import re
import sys
from pathlib import Path

SUPPORTED_STATEMENTS = {
    "ALTER",
    "BEGIN",
    "CALL",
    "CREATE",
    "DECLARE",
    "DELETE",
    "END",
    "INSERT",
    "MERGE",
    "SELECT",
    "SET",
    "UPDATE",
}


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


def sql_files(paths):
    if paths:
        return [Path(path) for path in paths]
    return sorted(
        path for path in Path(".").rglob("*.sql") if ".git" not in path.parts
    )


if __name__ == "__main__":
    files = sql_files(sys.argv[1:])
    if not files:
        raise SystemExit("SQL validation failed: no .sql files found")
    try:
        for path in files:
            validate_sql(path)
            print(f"SQL validation passed: {path}")
    except (OSError, ValueError) as error:
        raise SystemExit(f"SQL validation failed: {error}")
