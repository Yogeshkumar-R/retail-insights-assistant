"""
Validation Agent: Checks query results for validity and relevance.
Triggers retry if results are empty, contain errors, or are clearly wrong.
"""
import pandas as pd


CANNOT_ANSWER_MARKER = "CANNOT_ANSWER"


def validate_results(
    df: pd.DataFrame,
    sql: str,  # noqa: ARG001
    error: str | None,
) -> tuple[bool, str]:
    """
    Validate query results.
    Returns (is_valid: bool, reason: str).
    """
    # 1. SQL execution error
    if error:
        return False, f"SQL error: {error}"

    # 2. Empty result set
    if df.empty:
        return False, "Query returned no results. The data may not exist or the filter is too restrictive."

    # 3. CANNOT_ANSWER marker from LLM
    if df.shape == (1, 1):
        val = str(df.iloc[0, 0])
        if CANNOT_ANSWER_MARKER in val:
            return False, "out_of_scope"

    # 4. All values are NaN
    if df.isnull().all().all():
        return False, "Query returned only NULL values."

    # 5. Sanity check: negative revenue (data quality issue)
    for col in df.columns:
        if "amount" in col.lower() or "revenue" in col.lower() or "sales" in col.lower():
            numeric = pd.to_numeric(df[col], errors="coerce")
            if (numeric < 0).any():
                # Not a hard failure, just a warning — still valid
                pass

    return True, "ok"
