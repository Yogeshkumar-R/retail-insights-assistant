"""
Query Resolution Agent: Translates natural language questions into DuckDB SQL.
Uses Gemini LLM with schema injection and few-shot examples.
"""
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, DATASETS
from data.loader import get_schema_info
from prompts.query_prompt import QUERY_SYSTEM_PROMPT, QUERY_RETRY_PROMPT


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
    )


def _clean_sql(raw: str) -> str:
    """Strip markdown fences and whitespace from LLM output."""
    raw = raw.strip()
    # Remove ```sql ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def generate_sql(question: str, history: str) -> str:
    """
    Generate a DuckDB SQL query from a natural language question.
    Returns the SQL string.
    """
    schema = get_schema_info()
    prompt = QUERY_SYSTEM_PROMPT.format(
        schema=schema,
        history=history,
        question=question,
    )
    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return _clean_sql(response.content)


def retry_sql(question: str, previous_sql: str, error: str) -> str:
    """
    Retry SQL generation after a failure, providing the error context.
    """
    table_names = ", ".join(DATASETS.keys())
    prompt = QUERY_RETRY_PROMPT.format(
        question=question,
        error=error,
        previous_sql=previous_sql,
        table_names=table_names,
    )
    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return _clean_sql(response.content)
