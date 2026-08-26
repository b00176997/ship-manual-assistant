"""System settings. Adjust here to tune behavior."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
MANUALS_DIR = BASE_DIR / "manuals"      # uploaded PDFs are stored here
DB_DIR = BASE_DIR / "chroma_db"         # local vector database (works offline)
MANUALS_DIR.mkdir(exist_ok=True)

# --- Semantic search (embeddings) ---
# High-quality English retrieval model. Runs locally and offline.
# Downloaded once on first run (~1.3 GB), then everything is local.
# Uses the GPU automatically if an NVIDIA card is available (much faster indexing).
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")

# bge models want an instruction prefix on the QUERY only; passages get none.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
PASSAGE_PREFIX = ""

COLLECTION_NAME = "ship_manuals"

CHUNK_SIZE = 1000       # size of one semantic chunk (characters)
CHUNK_OVERLAP = 150     # overlap between chunks so context isn't lost at the seams
TOP_K = 6               # how many relevant chunks to retrieve per question

# --- OCR for scanned PDFs ---
# If a PDF is a scan (images, no text layer), add a text layer automatically.
# Needs the Tesseract engine installed; if it's missing, scans are skipped with a note.
OCR_ENABLED = True
OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "eng")  # e.g. "eng" or "eng+rus"

# --- Token saving: route a question to the most relevant manual(s) first ---
# Two-stage retrieval, all local (free): pick the document, then search inside it.
# Fewer, more on-target chunks go to Claude -> fewer input tokens, better precision.
ROUTE_DOCS = True
ROUTE_TOP_DOCS = 2        # how many manuals to consider per question
TOP_K_ROUTED = 4          # chunks sent to Claude when routing narrowed the search (vs TOP_K)
DOC_MAPS_COLLECTION = "ship_manual_docmaps"

# --- Answer generation (requires internet) ---
# Cheaper than Opus, quality is nearly identical for Q&A over manuals.
# To switch models, just change this one line (e.g. "claude-opus-4-8" or "claude-haiku-4-5").
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
CLAUDE_MAX_TOKENS = 8000
USE_THINKING = True     # adaptive reasoning — more accurate answers over technical docs

# Answer backend: "claude" (online) or "local" (offline via Ollama).
# Set automatically by the search-depth choice — the "Offline AI" depth uses local.
AI_BACKEND = "claude"

# --- Local offline model (Ollama) for the "Offline AI" mode ---
# Install Ollama from https://ollama.com ; setup.bat pulls this model.
# qwen2.5:7b fits an 8 GB GPU (e.g. laptop RTX 4060).
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Price per 1,000,000 tokens (USD), used to show the cost of each query.
PRICING = {
    "claude-opus-4-8":  {"in": 5.0, "out": 25.0},
    "claude-opus-4-7":  {"in": 5.0, "out": 25.0},
    "claude-sonnet-4-6": {"in": 3.0, "out": 15.0},
    "claude-haiku-4-5": {"in": 1.0, "out": 5.0},
}

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
