"""Command-line interface for OpenLegalDK."""

import argparse
import json
from pathlib import Path
import sys
import webbrowser

from . import find_citations, find_citations_with_sources


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="openlegaldk",
        description="Extract Danish and EU legal citations and link GDPR articles to EUR-Lex.",
    )
    parser.add_argument(
        "file", nargs="?", type=Path, help="UTF-8 text file (reads stdin by default)"
    )
    parser.add_argument("--pretty", action="store_true", help="Indent output JSON")
    parser.add_argument(
        "--language", choices=("DA", "EN"), default="DA",
        help="EUR-Lex document language for generated links (default: DA)",
    )
    parser.add_argument(
        "--no-links", action="store_true",
        help="Return the original citation-only JSON without official source links",
    )
    parser.add_argument(
        "--open-first-source", action="store_true",
        help="Open the first linked official EUR-Lex document in your browser",
    )
    parser.add_argument(
        "--fetch-articles", action="store_true",
        help="Try to download cited GDPR article text from EUR-Lex (network request)",
    )
    parser.add_argument(
        "--strict-fetch", action="store_true",
        help="Exit with status 2 if any requested GDPR article text cannot be retrieved",
    )
    parser.add_argument(
        "--timeout", type=float, default=12.0,
        help="EUR-Lex request timeout in seconds (default: 12, maximum: 60)",
    )
    args = parser.parse_args()
    if args.fetch_articles and args.no_links:
        parser.error("--fetch-articles cannot be used with --no-links")
    if args.strict_fetch and not args.fetch_articles:
        parser.error("--strict-fetch requires --fetch-articles")
    if not 0 < args.timeout <= 60:
        parser.error("--timeout must be greater than 0 and at most 60")
    try:
        content = args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))

    if args.no_links:
        result = [item.to_dict() for item in find_citations(content)]
    else:
        result = find_citations_with_sources(
            content, language=args.language,
            fetch_articles=args.fetch_articles, timeout=args.timeout,
        )

    if args.open_first_source:
        url = next((item["official_source"]["url"] for item in result
                    if "official_source" in item), None)
        if not url:
            parser.error("No supported official source link found. Try a GDPR citation.")
        webbrowser.open_new_tab(url)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    if args.strict_fetch and any(
        item.get("official_source", {}).get("fetch_status") == "unavailable"
        for item in result
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
