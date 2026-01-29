"""Relational table metadata schema and loading."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ColumnMetadata:
    """Metadata for a single column."""

    name: str
    data_type: str | None = None
    nullable: bool = True
    is_primary_key: bool = False

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ColumnMetadata:
        name = d.get("name") or d.get("column_name")
        if not name:
            raise ValueError("Column must have 'name' or 'column_name'")
        return cls(
            name=str(name).strip(),
            data_type=d.get("data_type") or d.get("type"),
            nullable=d.get("nullable", True),
            is_primary_key=bool(d.get("is_primary_key", False)),
        )


@dataclass
class TableMetadata:
    """Metadata for a single table (schema + columns)."""

    table_name: str
    schema_name: str | None = None
    columns: list[ColumnMetadata] = field(default_factory=list)
    primary_key_columns: list[str] | None = None

    @property
    def qualified_name(self) -> str:
        """Fully qualified table name (schema.table or table)."""
        if self.schema_name:
            return f"{self.schema_name}.{self.table_name}"
        return self.table_name

    @property
    def key_columns(self) -> list[str]:
        """Column names to use as key for ordering/joining (PK or first column)."""
        if self.primary_key_columns:
            return [c for c in self.primary_key_columns if c in self.column_names]
        pk_from_cols = [c.name for c in self.columns if c.is_primary_key]
        if pk_from_cols:
            return pk_from_cols
        return self.column_names[:1] if self.column_names else []

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TableMetadata:
        table_name = d.get("table_name") or d.get("table") or d.get("name")
        if not table_name:
            raise ValueError("Table must have 'table_name', 'table', or 'name'")
        cols = d.get("columns", [])
        if not cols and "column_names" in d:
            cols = [{"name": n} for n in d["column_names"]]
        columns = [ColumnMetadata.from_dict(c) for c in cols]
        return cls(
            table_name=str(table_name).strip(),
            schema_name=d.get("schema_name") or d.get("schema"),
            columns=columns,
            primary_key_columns=d.get("primary_key") or d.get("primary_key_columns"),
        )

    @classmethod
    def load(cls, path: str | Path) -> TableMetadata:
        """Load table metadata from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Metadata file not found: {path}")
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, list):
            data = {"table_name": "table", "columns": data}
        elif "columns" not in data and "column_names" not in data:
            raise ValueError("Metadata must contain 'columns' or 'column_names'")
        return cls.from_dict(data)
