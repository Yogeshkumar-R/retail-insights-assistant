"""
DuckDB setup and CSV data loader.
Loads all sales CSVs as virtual tables into an in-memory DuckDB connection.
"""
from pathlib import Path

import duckdb
import pandas as pd

from config import DATASETS


class _State:
    """Holds the shared DuckDB connection and schema info as mutable attributes."""

    conn: duckdb.DuckDBPyConnection | None = None
    schema_info: str = ""


_state = _State()


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return (or create) the shared DuckDB connection with all tables loaded."""
    if _state.conn is not None:
        return _state.conn

    _state.conn = duckdb.connect(database=":memory:")

    schema_parts = []
    for table_name, file_path in DATASETS.items():
        path = Path(file_path)
        if not path.exists():
            print(f"[loader] WARNING: {path} not found, skipping.")
            continue
        try:
            # Read CSV with pandas first to handle encoding issues
            df = pd.read_csv(path, encoding="unicode_escape", low_memory=False)
            # Clean column names: lowercase, replace spaces/special chars with underscores
            df.columns = [
                c.strip().lower()
                 .replace(" ", "_")
                 .replace("-", "_")
                 .replace(".", "_")
                 .replace("(", "")
                 .replace(")", "")
                 .replace("/", "_")
                for c in df.columns
            ]
            # Register as a DuckDB view
            _state.conn.register(table_name, df)
            # Build schema description
            col_info = ", ".join(f"{col} ({dtype})" for col, dtype in zip(df.columns, df.dtypes))
            sample = df.head(2).to_dict(orient="records")
            schema_parts.append(
                f"Table: {table_name}\n"
                f"  Columns: {col_info}\n"
                f"  Sample rows: {sample}\n"
            )
            print(f"[loader] Loaded '{table_name}' — {len(df)} rows, {len(df.columns)} cols")
        except (pd.errors.ParserError, UnicodeDecodeError, duckdb.Error, OSError) as e:
            print(f"[loader] ERROR loading {table_name}: {e}")

    _state.schema_info = "\n".join(schema_parts)
    return _state.conn


def get_schema_info() -> str:
    """Return a text description of all loaded tables and their columns."""
    if not _state.schema_info:
        get_connection()  # ensure loaded
    return _state.schema_info


def execute_query(sql: str) -> pd.DataFrame:
    """Execute a SQL query and return results as a DataFrame."""
    conn = get_connection()
    try:
        result = conn.execute(sql).fetchdf()
        return result
    except duckdb.Error as e:
        raise ValueError(f"SQL execution error: {e}") from e
