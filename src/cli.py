"""CLI for the comparison agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .comparison_agent import generate_comparison_selects
from .metadata import TableMetadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate two SELECT statements to compare source and target tables from metadata files."
    )
    parser.add_argument(
        "source_metadata",
        type=Path,
        help="Path to source table metadata JSON file",
    )
    parser.add_argument(
        "target_metadata",
        type=Path,
        help="Path to target table metadata JSON file",
    )
    parser.add_argument(
        "--no-intersection",
        action="store_true",
        help="Use all source columns (target may have fewer; not recommended for comparison)",
    )
    parser.add_argument(
        "--no-order-by",
        action="store_true",
        help="Omit ORDER BY on key columns",
    )
    parser.add_argument(
        "--dialect",
        choices=["ansi", "sqlserver", "mssql", "mysql"],
        default="ansi",
        help="SQL dialect for identifiers (default: ansi)",
    )
    parser.add_argument(
        "--quoted",
        action="store_true",
        help="Use quoted identifiers (ANSI double-quote style)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write SQL to file (default: stdout)",
    )
    args = parser.parse_args()

    try:
        source = TableMetadata.load(args.source_metadata)
        target = TableMetadata.load(args.target_metadata)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        source_sql, target_sql = generate_comparison_selects(
            source,
            target,
            use_intersection=not args.no_intersection,
            order_by_keys=not args.no_order_by,
            dialect=args.dialect,
            use_quoted_identifiers=args.quoted,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    out = f"-- Source table: {source.qualified_name}\n{source_sql}\n\n-- Target table: {target.qualified_name}\n{target_sql}\n"
    if args.output:
        args.output.write_text(out, encoding="utf-8")
        print(f"Wrote comparison SQL to {args.output}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
