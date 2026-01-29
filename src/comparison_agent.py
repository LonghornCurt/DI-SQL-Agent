"""Agent that generates two SELECT statements to compare source and target tables from metadata."""

from __future__ import annotations

from .metadata import TableMetadata


def align_columns(
    source: TableMetadata,
    target: TableMetadata,
    use_intersection: bool = True,
) -> list[str]:
    """
    Determine column list for comparison SELECTs.

    - use_intersection=True: only columns present in both tables (default).
    - use_intersection=False: all columns from source; target SELECT uses same order,
      missing columns as NULL.
    """
    src_names = set(source.column_names)
    tgt_names = set(target.column_names)
    if use_intersection:
        common = src_names & tgt_names
        # Preserve source table column order for consistency
        return [c for c in source.column_names if c in common]
    return source.column_names


def quote_identifier(name: str, dialect: str = "ansi") -> str:
    """Quote identifier for SQL (e.g. reserved words, case)."""
    if dialect == "ansi" or dialect == "ansi_quoted":
        return f'"{name}"' if dialect == "ansi_quoted" else name
    if dialect in ("sqlserver", "mssql"):
        return f"[{name}]"
    if dialect == "mysql":
        return f"`{name}`"
    return name


def build_select(
    table: TableMetadata,
    columns: list[str],
    order_by_columns: list[str] | None = None,
    dialect: str = "ansi",
    use_quoted_identifiers: bool = False,
) -> str:
    """Build a single SELECT statement for the given table and column list."""
    quote = (
        (lambda c: quote_identifier(c, "ansi_quoted"))
        if use_quoted_identifiers
        else (lambda c: quote_identifier(c, dialect))
    )
    qualified = table.qualified_name
    if use_quoted_identifiers and table.schema_name:
        qualified = f'"{table.schema_name}"."{table.table_name}"'
    elif dialect == "sqlserver" and table.schema_name:
        qualified = f"[{table.schema_name}].[{table.table_name}]"

    select_list = ", ".join(quote(c) for c in columns)
    sql = f"SELECT {select_list}\nFROM {qualified}"
    if order_by_columns:
        order_list = ", ".join(quote(c) for c in order_by_columns)
        sql += f"\nORDER BY {order_list}"
    return sql


def generate_comparison_selects(
    source_metadata: TableMetadata,
    target_metadata: TableMetadata,
    *,
    use_intersection: bool = True,
    order_by_keys: bool = True,
    dialect: str = "ansi",
    use_quoted_identifiers: bool = False,
) -> tuple[str, str]:
    """
    Generate two SELECT statements to compare source and target tables.

    Returns:
        (source_select_sql, target_select_sql) with aligned columns and optional ORDER BY
        so result sets can be diffed or used with EXCEPT/INTERSECT.
    """
    columns = align_columns(source_metadata, target_metadata, use_intersection=use_intersection)
    if not columns:
        raise ValueError(
            "No common columns between source and target. "
            f"Source: {source_metadata.column_names}, Target: {target_metadata.column_names}"
        )

    order_cols: list[str] | None = None
    if order_by_keys:
        src_keys = source_metadata.key_columns
        tgt_keys = target_metadata.key_columns
        # Use key columns that are in our selected column list
        order_cols = [k for k in (src_keys or tgt_keys) if k in columns]
        if not order_cols and columns:
            order_cols = columns[:1]

    source_sql = build_select(
        source_metadata,
        columns,
        order_by_columns=order_cols,
        dialect=dialect,
        use_quoted_identifiers=use_quoted_identifiers,
    )
    target_sql = build_select(
        target_metadata,
        columns,
        order_by_columns=order_cols,
        dialect=dialect,
        use_quoted_identifiers=use_quoted_identifiers,
    )
    return source_sql, target_sql
