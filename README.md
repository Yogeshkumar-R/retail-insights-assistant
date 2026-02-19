# 🛍️ Retail Insights Assistant

A **GenAI-powered multi-agent chatbot** for analyzing retail sales data using natural language.

## Features

- 💬 **Conversational Q&A** — Ask questions like *"Which category had the highest sales?"*
- 📊 **Auto Summary** — Generate executive-level business summaries with charts
- 🤖 **Multi-Agent Pipeline** — 5 specialized agents orchestrated by LangGraph
- 🦆 **DuckDB Backend** — Fast in-process SQL over CSV files (no database setup)
- 🧠 **Conversation Memory** — Follow-up questions maintain context

## Architecture

```
User Query
    ↓
Orchestrator (LangGraph)
    ↓
Query Resolution Agent  →  NL → SQL (Gemini)
    ↓
Data Extraction Agent   →  Execute SQL (DuckDB)
    ↓
Validation Agent        →  Check results / retry
    ↓
Summary Agent           →  SQL results → Business insight (Gemini)
    ↓
User Response
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key_here
```

Get a free API key at [Google AI Studio](https://aistudio.google.com/).

### 3. Run the App

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

## Dataset

Place the CSV files in `Sales Dataset/Sales Dataset/`:

| File | Description |
|---|---|
| `Amazon Sale Report.csv` | Main domestic sales (~128k orders) |
| `International sale Report.csv` | International orders |
| `Sale Report.csv` | Inventory / stock levels |
| `May-2022.csv` | Platform MRP comparison (May 2022) |
| `P  L March 2021.csv` | P&L / cost data (March 2021) |
| `Cloud Warehouse Compersion Chart.csv` | Logistics comparison |
| `Expense IIGF.csv` | Expense tracking |

## Example Questions

- *"Which category had the highest total revenue?"*
- *"What are the top 5 states by order volume?"*
- *"How many orders were cancelled?"*
- *"What is the total international revenue?"*
- *"Which product size sells the most?"*
- *"Show me stock levels by category"*

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| LLM | Google Gemini 2.5 Flash |
| Agent Framework | LangGraph |
| Data Layer | DuckDB + Pandas |
| UI | Streamlit |
| Memory | Custom sliding-window buffer |

## Assumptions & Limitations

- The `amount` column in Amazon Sales may contain non-numeric values; these are coerced to NaN.
- Date filtering uses DuckDB's string parsing; complex date ranges may need rephrasing.
- The assistant is scoped to the provided CSV datasets only.
- For 100GB+ scale, see the Architecture Presentation for the cloud-native design.

## Scalability (100GB+)

For production scale, the architecture uses:
- **PySpark / Databricks** for ETL
- **Parquet on S3/GCS** for storage
- **BigQuery / Snowflake** for analytical queries
- **Pinecone / ChromaDB** for vector search (RAG)
- **Redis** for prompt caching
- **LangSmith** for monitoring

  ## try demo: [App](https://retains.streamlit.app/)
