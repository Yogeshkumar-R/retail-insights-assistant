"""
Summary Agent: Converts raw query results into human-readable business insights.
Uses Gemini LLM with a business analyst persona.
"""
import json
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, MAX_RESULT_ROWS
from prompts.summary_prompt import SUMMARY_SYSTEM_PROMPT, SUMMARIZATION_SYSTEM_PROMPT


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
    )


def generate_insight(question: str, df: pd.DataFrame, history: str) -> str:
    """
    Generate a business insight from query results.
    """
    # Truncate large result sets
    if len(df) > MAX_RESULT_ROWS:
        df = df.head(MAX_RESULT_ROWS)

    # Convert to JSON for prompt injection
    try:
        results_json = df.to_json(orient="records", default_handler=str)
    except (ValueError, TypeError):
        results_json = df.to_string()

    prompt = SUMMARY_SYSTEM_PROMPT.format(
        history=history,
        question=question,
        results=results_json,
    )
    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def generate_full_summary(amazon_df: pd.DataFrame, intl_df: pd.DataFrame) -> str:
    """
    Generate an executive summary from the main sales datasets.
    Used for Summarization Mode.
    """
    # Compute key stats
    stats = {}

    # Amazon sales stats
    try:
        amount_series = amazon_df.get("amount", pd.Series())
        amazon_df["amount_num"] = pd.to_numeric(amount_series, errors="coerce")
        stats["total_amazon_revenue"] = f"₹{amazon_df['amount_num'].sum():,.0f}"
        stats["total_amazon_orders"] = len(amazon_df)
        stats["top_categories"] = (
            amazon_df.groupby("category")["amount_num"]
            .sum()
            .nlargest(5)
            .to_dict()
        )
        stats["top_states"] = (
            amazon_df.groupby("ship_state")["amount_num"]
            .sum()
            .nlargest(5)
            .to_dict()
        )
        stats["order_status_breakdown"] = (
            amazon_df["status"].value_counts().head(5).to_dict()
        )
    except (KeyError, ValueError, TypeError) as e:
        stats["amazon_error"] = str(e)

    # International sales stats
    try:
        intl_df["gross_amt_num"] = pd.to_numeric(
            intl_df.get("gross_amt", pd.Series()), errors="coerce"
        )
        intl_total = intl_df['gross_amt_num'].sum()
        stats["total_international_revenue"] = f"${intl_total:,.0f}"
        stats["total_international_orders"] = len(intl_df)
    except (KeyError, ValueError, TypeError) as e:
        stats["intl_error"] = str(e)

    data_summary = json.dumps(stats, indent=2, default=str)
    prompt = SUMMARIZATION_SYSTEM_PROMPT.format(data_summary=data_summary)

    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
