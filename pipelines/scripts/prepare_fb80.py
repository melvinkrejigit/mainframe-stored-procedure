"""Prepare SQL as fixed 80-character records with SQL in columns 1-72."""
import sys
from pathlib import Path


def prepare(source: Path, destination: Path) -> None:
    text = source.read_text(encoding="utf-8-sig")
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) > 72:
            raise ValueError(f"{source}: line {number} has {len(line)} characters; maximum is 72")
        records.append(line.ljust(80))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(records) + ("\n" if records else ""), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_fb80.py <input.sql> <output-file>")
    try:
        prepare(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, ValueError) as error:
        raise SystemExit(f"FB80 preparation failed: {error}")
    print(f"Prepared {sys.argv[1]} as FB80 text")
