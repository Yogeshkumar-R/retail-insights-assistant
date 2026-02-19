"""
Data Extraction Agent: Executes SQL queries against DuckDB and returns results.
"""
import duckdb
import pandas as pd
from data.loader import execute_query


def run_query(sql: str) -> tuple[pd.DataFrame, str | None]:
    """
    Execute a SQL query.
    Returns (DataFrame, error_message). If successful, error_message is None.
    """
    try:
        df = execute_query(sql)
        return df, None
    except (duckdb.Error, ValueError) as e:
        return pd.DataFrame(), str(e)
