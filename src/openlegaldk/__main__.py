"""Command-line interface for OpenLegalDK."""

import argparse
import json
from pathlib import Path
import sys

from . import find_citations


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="openlegaldk",
        description="Extract Danish and EU legal citation patterns from text.",
    )
    parser.add_argument(
        "file", nargs="?", type=Path, help="UTF-8 text file (reads stdin by default)"
    )
    parser.add_argument("--pretty", action="store_true", help="Indent output JSON")
    args = parser.parse_args()
    try:
        content = args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))

    result = [item.to_dict() for item in find_citations(content)]
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
