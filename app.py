"""
Streamlit UI for the Retail Insights Assistant.
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import os

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Insights Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    .main-header h1 { font-size: 2rem; font-weight: 700; margin: 0; }
    .main-header p  { font-size: 1rem; opacity: 0.85; margin: 0.5rem 0 0; }

    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        text-align: center;
        border: 1px solid #e0e0e0;
    }

    .chat-user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
    }

    .chat-assistant {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 18px 18px 18px 4px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        max-width: 85%;
    }

    .sql-expander {
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: opacity 0.2s;
    }

    .stButton > button:hover { opacity: 0.85; }

    .sidebar-section {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    from memory.conversation import ConversationMemory
    st.session_state.memory = ConversationMemory()
if "db_loaded" not in st.session_state:
    st.session_state.db_loaded = False
if "api_key_set" not in st.session_state:
    st.session_state.api_key_set = bool(os.getenv("GOOGLE_API_KEY"))


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ Retail Insights")
    st.markdown("---")

    # API Key input
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=os.getenv("GOOGLE_API_KEY", ""),
        help="Get your key at https://aistudio.google.com/",
        key="api_key_input",
    )
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.session_state.api_key_set = True

    st.markdown("---")

    # Dataset status
    st.markdown("### 📁 Dataset Status")
    if st.button("🔄 Load / Reload Data", use_container_width=True):
        with st.spinner("Loading datasets into DuckDB..."):
            try:
                from data.loader import get_connection, get_schema_info
                get_connection()
                st.session_state.db_loaded = True
                st.success("✅ Data loaded successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if st.session_state.db_loaded:
        st.markdown('<div class="sidebar-section">✅ DuckDB ready with 7 tables</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Quick questions
    st.markdown("### 💡 Sample Questions")
    sample_questions = [
        "Which category had the highest sales?",
        "What are the top 5 states by revenue?",
        "How many orders were cancelled?",
        "What is the total international revenue?",
        "Which product size sells the most?",
        "Show me stock levels by category",
    ]
    for q in sample_questions:
        if st.button(q, key=f"sample_{q[:20]}", use_container_width=True):
            st.session_state["prefill_question"] = q

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.rerun()


# ─── Main Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛍️ Retail Insights Assistant</h1>
    <p>GenAI-powered analytics • Multi-agent • Natural Language Q&A</p>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_chat, tab_summary, tab_schema = st.tabs(["💬 Chat Q&A", "📊 Auto Summary", "🗄️ Data Schema"])


# ─── Tab 1: Chat Q&A ──────────────────────────────────────────────────────────
with tab_chat:
    if not st.session_state.api_key_set:
        st.warning("⚠️ Please enter your Google Gemini API key in the sidebar to get started.")
    elif not st.session_state.db_loaded:
        st.info("👈 Click **Load / Reload Data** in the sidebar to initialize the database.")
    else:
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-assistant">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
                    if msg.get("sql"):
                        with st.expander("🔍 View SQL Query", expanded=False):
                            st.code(msg["sql"], language="sql")
                    if msg.get("dataframe") is not None and not msg["dataframe"].empty:
                        with st.expander("📋 View Raw Data", expanded=False):
                            st.dataframe(msg["dataframe"], use_container_width=True)

        # Input
        prefill = st.session_state.pop("prefill_question", "")
        question = st.chat_input(
            placeholder="Ask anything about your sales data...",
        ) or prefill

        if question:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.memory.add_user(question)

            with st.spinner("🤖 Agents working..."):
                try:
                    from agents.orchestrator import run_qa_pipeline
                    history = st.session_state.memory.get_formatted()
                    result = run_qa_pipeline(question=question, history=history)

                    answer = result.get("final_answer", "Sorry, I couldn't process that.")
                    sql = result.get("sql", "")
                    df = result.get("result_df", pd.DataFrame())

                    st.session_state.memory.add_assistant(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sql": sql,
                        "dataframe": df,
                    })
                except Exception as e:
                    error_msg = f"An error occurred: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            st.rerun()


# ─── Tab 2: Auto Summary ──────────────────────────────────────────────────────
with tab_summary:
    st.markdown("### 📊 Executive Sales Summary")
    st.markdown("Generate an AI-powered summary of your overall sales performance.")

    if not st.session_state.api_key_set:
        st.warning("⚠️ Please enter your Google Gemini API key in the sidebar.")
    elif not st.session_state.db_loaded:
        st.info("👈 Click **Load / Reload Data** in the sidebar first.")
    else:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("✨ Generate Summary", use_container_width=True):
                with st.spinner("Analyzing data and generating insights..."):
                    try:
                        from data.loader import execute_query
                        from agents.summary_agent import generate_full_summary

                        amazon_df = execute_query("SELECT * FROM amazon_sales LIMIT 10000")
                        intl_df = execute_query("SELECT * FROM international_sales LIMIT 5000")

                        # Show quick metrics
                        st.session_state["summary_amazon_df"] = amazon_df
                        st.session_state["summary_intl_df"] = intl_df
                        summary = generate_full_summary(amazon_df, intl_df)
                        st.session_state["auto_summary"] = summary
                    except Exception as e:
                        st.error(f"Error generating summary: {e}")

        if "auto_summary" in st.session_state:
            # Quick metrics row
            amazon_df = st.session_state.get("summary_amazon_df", pd.DataFrame())
            intl_df = st.session_state.get("summary_intl_df", pd.DataFrame())

            m1, m2, m3, m4 = st.columns(4)
            try:
                total_rev = pd.to_numeric(amazon_df.get("amount", pd.Series()), errors="coerce").sum()
                m1.metric("💰 Total Amazon Revenue", f"₹{total_rev:,.0f}")
                m2.metric("📦 Total Orders", f"{len(amazon_df):,}")
                top_cat = amazon_df.groupby("category")["amount"].apply(
                    lambda x: pd.to_numeric(x, errors="coerce").sum()
                ).idxmax()
                m3.metric("🏆 Top Category", str(top_cat))
                intl_rev = pd.to_numeric(intl_df.get("gross_amt", pd.Series()), errors="coerce").sum()
                m4.metric("🌍 International Revenue", f"${intl_rev:,.0f}")
            except Exception:
                pass

            st.markdown("---")
            st.markdown("#### 🤖 AI-Generated Insights")
            st.markdown(st.session_state["auto_summary"])

            # Charts
            st.markdown("---")
            st.markdown("#### 📈 Visual Breakdown")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                try:
                    cat_data = amazon_df.copy()
                    cat_data["amount_num"] = pd.to_numeric(cat_data["amount"], errors="coerce")
                    cat_chart = cat_data.groupby("category")["amount_num"].sum().nlargest(8).reset_index()
                    cat_chart.columns = ["Category", "Revenue"]
                    st.markdown("**Revenue by Category**")
                    st.bar_chart(cat_chart.set_index("Category"))
                except Exception:
                    pass

            with chart_col2:
                try:
                    state_data = amazon_df.copy()
                    state_data["amount_num"] = pd.to_numeric(state_data["amount"], errors="coerce")
                    state_chart = state_data.groupby("ship_state")["amount_num"].sum().nlargest(8).reset_index()
                    state_chart.columns = ["State", "Revenue"]
                    st.markdown("**Revenue by State (Top 8)**")
                    st.bar_chart(state_chart.set_index("State"))
                except Exception:
                    pass


# ─── Tab 3: Schema ────────────────────────────────────────────────────────────
with tab_schema:
    st.markdown("### 🗄️ Available Data Tables")
    if not st.session_state.db_loaded:
        st.info("👈 Click **Load / Reload Data** in the sidebar to see the schema.")
    else:
        from data.loader import get_schema_info, execute_query
        from config import DATASETS

        for table_name in DATASETS.keys():
            try:
                df_preview = execute_query(f"SELECT * FROM {table_name} LIMIT 5")
                with st.expander(f"📋 `{table_name}` — {len(df_preview.columns)} columns", expanded=False):
                    st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not preview `{table_name}`: {e}")
