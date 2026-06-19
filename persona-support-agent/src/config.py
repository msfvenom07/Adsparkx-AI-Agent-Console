import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "chroma_db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# Model configuration
DEFAULT_LLM_MODEL = "gemini-2.5-flash"  # standard fast model
DEFAULT_CLASSIFIER_MODEL = "gemini-2.5-flash"  # stable classification model
DEFAULT_EMBEDDING_MODEL = "text-embedding-004"
LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# RAG & Chunking
CHUNK_SIZE = 400
CHUNK_OVERLAP = 40
TOP_K = 3

# Escalation settings
SIMILARITY_THRESHOLD = 0.40  # Minimum similarity score to consider retrieval grounded
MAX_CONVERSATION_TURNS = 3   # Max turns user can be frustrated/negative before escalation

# Sensitive topics that trigger immediate human escalation
SENSITIVE_KEYWORDS = [
    "billing", 
    "refund", 
    "chargeback", 
    "duplicate charge", 
    "overcharged", 
    "payment failure", 
    "cancel subscription", 
    "close account", 
    "delete account", 
    "legal", 
    "sue", 
    "lawyer", 
    "court", 
    "fraud", 
    "scam", 
    "stolen credit card",
    "unauthorized transaction",
    "breach",
    "hacked",
    "security vulnerability"
]
