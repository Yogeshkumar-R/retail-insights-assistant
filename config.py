"""
Configuration for the Retail Insights Assistant.
Set your GOOGLE_API_KEY in a .env file or as an environment variable.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "Sales Dataset" / "Sales Dataset"

# Dataset files
DATASETS = {
    "amazon_sales": DATA_DIR / "Amazon Sale Report.csv",
    "international_sales": DATA_DIR / "International sale Report.csv",
    "sale_report": DATA_DIR / "Sale Report.csv",
    "may_2022": DATA_DIR / "May-2022.csv",
    "pl_march_2021": DATA_DIR / "P  L March 2021.csv",
    "cloud_warehouse": DATA_DIR / "Cloud Warehouse Compersion Chart.csv",
    "expense": DATA_DIR / "Expense IIGF.csv",
}

# --- LLM ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY is not set. "
        "Add it to your .env file or set it as an environment variable."
    )
GEMINI_MODEL = "gemini-2.5-flash"

# --- Agent settings ---
MAX_RETRIES = 3          # Max SQL retry attempts by validation agent
MAX_RESULT_ROWS = 50     # Max rows to pass to summary agent
MEMORY_WINDOW = 10       # Number of conversation turns to keep in memory
