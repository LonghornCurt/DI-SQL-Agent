# DI-SQL-Agent

Generate two **SELECT** statements to compare a source table to a target table from relational database metadata files. Use the output in your data integration pipeline to diff result sets or run `EXCEPT`/`INTERSECT` for reconciliation.

## Metadata format

Each metadata file is JSON describing one table:

- **table_name** (or `table`, `name`): table name
- **schema_name** (optional): schema
- **columns**: list of column definitions
- **primary_key** (optional): list of column names for the primary key

Each column can have:

- **name** (or `column_name`): column name
- **data_type** (optional)
- **nullable** (optional)
- **is_primary_key** (optional)

Minimal example:

```json
{
  "table_name": "Users",
  "columns": [
    { "name": "id", "is_primary_key": true },
    { "name": "email" }
  ]
}
```

## Installation

From the project root:

```bash
pip install -e .
```

## Usage

### CLI

```bash
di-sql-compare path/to/source_metadata.json path/to/target_metadata.json
```

Options:

- `--no-intersection` — use all source columns (default: use only columns present in both tables)
- `--no-order-by` — omit `ORDER BY` on key columns
- `--dialect ansi|sqlserver|mssql|mysql` — identifier quoting
- `--quoted` — use quoted identifiers (e.g. `"ColumnName"`)
- `-o file.sql` — write SQL to a file instead of stdout

Example with example metadata:

```bash
di-sql-compare examples/source_metadata.json examples/target_metadata.json
```

Output (conceptually):

```sql
-- Source table: dbo.Customers
SELECT id, name, email, created_at
FROM dbo.Customers
ORDER BY id

-- Target table: staging.customers
SELECT id, name, email, created_at
FROM staging.customers
ORDER BY id
```

Run both SELECTs in your DB (source and target), then compare the result sets (e.g. diff, or `EXCEPT` in SQL) to verify data alignment.

### Python API

```python
from src.metadata import TableMetadata
from src.comparison_agent import generate_comparison_selects

source = TableMetadata.load("examples/source_metadata.json")
target = TableMetadata.load("examples/target_metadata.json")

source_sql, target_sql = generate_comparison_selects(
    source, target,
    use_intersection=True,
    order_by_keys=True,
    dialect="ansi",
)
print(source_sql)
print(target_sql)
```

## Behavior

1. **Column alignment**  
   By default, only columns that exist in **both** source and target are included, in source column order. This keeps both SELECTs comparable.

2. **Ordering**  
   If primary key (or key columns) are set in metadata, both SELECTs get an `ORDER BY` on those columns so row order is deterministic for diffing.

3. **Dialects**  
   Identifier quoting can be set for ANSI, SQL Server, or MySQL so generated SQL is valid in your engine.

## License

MIT
