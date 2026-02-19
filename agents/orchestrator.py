"""
Orchestrator Agent: LangGraph-based multi-agent pipeline.
Defines the state graph connecting all agents.
"""
from typing import TypedDict
import pandas as pd
from langgraph.graph import StateGraph, END

from agents.query_agent import generate_sql, retry_sql
from agents.data_agent import run_query
from agents.validation_agent import validate_results
from agents.summary_agent import generate_insight
from prompts.summary_prompt import OUT_OF_SCOPE_RESPONSE
from config import MAX_RETRIES


# ─── State Definition ─────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """Shared state schema passed between all nodes in the LangGraph pipeline."""

    question: str
    history: str
    sql: str
    result_df: pd.DataFrame
    error: str | None
    is_valid: bool
    validation_reason: str
    final_answer: str
    retry_count: int


# ─── Node Functions ────────────────────────────────────────────────────────────

def query_resolution_node(state: AgentState) -> AgentState:
    """NL → SQL: Generate or retry SQL based on state."""
    if state.get("retry_count", 0) > 0 and state.get("sql"):
        # Retry with error context
        sql = retry_sql(
            question=state["question"],
            previous_sql=state["sql"],
            error=state.get("error", "Unknown error"),
        )
    else:
        sql = generate_sql(
            question=state["question"],
            history=state["history"],
        )
    return {**state, "sql": sql}


def data_extraction_node(state: AgentState) -> AgentState:
    """Execute SQL and capture results or errors."""
    df, error = run_query(state["sql"])
    return {**state, "result_df": df, "error": error}


def validation_node(state: AgentState) -> AgentState:
    """Validate results and decide if retry is needed."""
    is_valid, reason = validate_results(
        df=state.get("result_df", pd.DataFrame()),
        sql=state.get("sql", ""),
        error=state.get("error"),
    )
    return {**state, "is_valid": is_valid, "validation_reason": reason}


def summary_node(state: AgentState) -> AgentState:
    """Convert results into a business insight."""
    answer = generate_insight(
        question=state["question"],
        df=state["result_df"],
        history=state["history"],
    )
    return {**state, "final_answer": answer}


def out_of_scope_node(state: AgentState) -> AgentState:
    """Handle questions that can't be answered with available data."""
    return {**state, "final_answer": OUT_OF_SCOPE_RESPONSE}


def error_node(state: AgentState) -> AgentState:
    """Handle exhausted retries."""
    reason = state.get("validation_reason", "Unknown error")
    answer = (
        f"I wasn't able to retrieve the data for your question after {MAX_RETRIES} attempts.\n\n"
        f"**Reason**: {reason}\n\n"
        "Please try rephrasing your question or ask about a different metric."
    )
    return {**state, "final_answer": answer}


# ─── Routing Logic ─────────────────────────────────────────────────────────────

def route_after_validation(state: AgentState) -> str:
    """Decide next step after validation."""
    if state["is_valid"]:
        return "summary"
    if state.get("validation_reason") == "out_of_scope":
        return "out_of_scope"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "error"
    return "retry"


# ─── Graph Construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and compile the LangGraph multi-agent state graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("query_resolution", query_resolution_node)
    graph.add_node("data_extraction", data_extraction_node)
    graph.add_node("validation", validation_node)
    graph.add_node("summary", summary_node)
    graph.add_node("out_of_scope", out_of_scope_node)
    graph.add_node("error", error_node)

    # Entry point
    graph.set_entry_point("query_resolution")

    # Edges
    graph.add_edge("query_resolution", "data_extraction")
    graph.add_edge("data_extraction", "validation")
    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "summary": "summary",
            "out_of_scope": "out_of_scope",
            "error": "error",
            "retry": "query_resolution",
        },
    )
    graph.add_edge("summary", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("error", END)

    return graph.compile()


# ─── Public API ────────────────────────────────────────────────────────────────

_graph_cache: list = []


def get_graph():
    """Return the singleton compiled graph, building it on first call."""
    if not _graph_cache:
        _graph_cache.append(build_graph())
    return _graph_cache[0]


def run_qa_pipeline(question: str, history: str) -> dict:
    """
    Run the full Q&A multi-agent pipeline.
    Returns the final state dict with 'final_answer' and 'sql'.
    """
    graph = get_graph()
    initial_state: AgentState = {
        "question": question,
        "history": history,
        "sql": "",
        "result_df": pd.DataFrame(),
        "error": None,
        "is_valid": False,
        "validation_reason": "",
        "final_answer": "",
        "retry_count": 0,
    }
    final_state = graph.invoke(initial_state)
    return final_state
