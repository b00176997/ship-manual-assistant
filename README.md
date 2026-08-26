# ⚓ Ship Mechanic Assistant (RAG over PDF manuals)

Load your PDF manuals once, then ask questions like "How do I repair the main cock?"
or "How do I replace the valve seal?" — the system searches the documentation by
**meaning** and answers with references to the file and page.

## How it works (Variant 3 architecture)

```
PDF manuals
   │  text extraction (pypdf)
   ▼
Split into semantic chunks (with page tracking for citations)
   │  local model BAAI/bge-large-en-v1.5  ← RUNS OFFLINE, FREE, GPU-accelerated
   ▼
Vectors (embeddings)
   │
   ▼
Chroma vector database (on disk, offline)
   │
   ▼
Question → semantic search → top chunks → Claude API → answer with citations
                                                  ▲
                                       internet needed only here
```

**About offline use:** loading manuals and searching them work fully without internet.
Internet is only needed at the moment Claude generates the answer. If there is no
internet, the system still shows the retrieved manual excerpts (file + page) so the
mechanic can find what they need.

> Note: the Claude API has no embeddings endpoint — so vectors are produced by a local
> model. This is also better for a ship: offline and free.

## Embedding model

Default: **`BAAI/bge-large-en-v1.5`** — a high-quality English retrieval model (1024-dim).
It is downloaded once on first run (~1.3 GB) and then runs locally.

**Speed (GPU vs CPU):** indexing speed depends on hardware. `setup.bat` **automatically
installs the GPU build of PyTorch when an NVIDIA card is present**, and the app then runs
the model on the GPU. The difference is large:

| Hardware | 500-page manual |
|---|---|
| NVIDIA GPU (e.g. RTX 4070 Ti) | ~20 seconds |
| CPU only | ~30 minutes |

On an NVIDIA laptop you get top quality *and* speed. On a CPU-only machine the large
model is slow for big manuals — switch to a smaller model in `config.py`
(`EMBEDDING_MODEL=BAAI/bge-base-en-v1.5` or `...-small-...`) for acceptable CPU speed.

## Setup (Windows)

1. Install **Python 3.10–3.12** from https://python.org
   (tick "Add Python to PATH" during install).
   ⚠️ Very new Python (3.13/3.14) may not install `torch` yet — use 3.12.
2. Double-click **`setup.bat`** — installs everything (5–10 minutes).
3. Open the generated **`.env`** file and add your key:
   `ANTHROPIC_API_KEY=your_key`
   (the key is only needed for AI answers; search works without it).

## Running

Double-click **`start.bat`** — the browser opens with the app
(`http://127.0.0.1:5000`).

> **Tip — desktop shortcut:** run **`create_shortcut.bat`** once to put a
> "Ship Mechanic Assistant" icon on the Desktop. Use the shortcut, not a copy of
> `start.bat` (a copy won't find its files). The shortcut is machine-specific, so
> run `create_shortcut.bat` again on each computer.

Then:

1. Drag PDF manuals into the upload area (or pick a file).
   The first run downloads the search model (~1.3 GB) — internet needed **once**.
2. Type a question and click "Ask".

### Many manuals at once

Putting PDFs in the `manuals/` folder is **not enough on its own** — they must be
indexed first. The easy way:

1. Copy all your PDFs into the **`manuals`** folder.
2. Double-click **`index_manuals.bat`**.

It indexes every PDF in the folder and **skips ones already indexed**, so you can keep
adding new manuals and re-run it any time. (Re-run with `python ingest_folder.py --force`
to rebuild everything from scratch.) You can still drag PDFs into the web page one by one
for a few files.

## Scale

A library of ~2000 pages produces roughly 5,000–8,000 chunks (~25 MB on disk) — trivial
for Chroma, and search stays near-instant. The index is stored on **disk** (the
`chroma_db/` folder), not in RAM, so it persists between runs: load the manuals once and
they stay indexed.

## Project files

| File | Purpose |
|------|---------|
| `app.py` | Web app (Flask) |
| `chunking.py` | PDF text extraction and chunking |
| `embeddings.py` | Local vectorization model (offline, GPU-aware) |
| `ingest.py` | Loads PDFs into the Chroma vector database |
| `search.py` | Semantic search |
| `rag.py` | Builds the answer via Claude with citations |
| `ingest_folder.py` | Bulk-load a folder of PDFs |
| `config.py` | Settings (model, chunk size, top-k, etc.) |

## Tuning

Everything is in `config.py`:
- `TOP_K` — how many chunks feed the answer (more = fuller, but slower).
- `CHUNK_SIZE` / `CHUNK_OVERLAP` — chunk sizing.
- `USE_THINKING` — Claude "thinking" mode (more accurate, slightly slower).
- `EMBEDDING_MODEL` — the search model.

> The index records which embedding model built it. If you change `EMBEDDING_MODEL`,
> the app **detects the mismatch automatically**, shows a warning banner, and offers a
> one-click **"Re-index now"** button — your PDFs stay in `manuals/`, so nothing needs
> re-uploading. (You can also re-index from the console with `python ingest_folder.py`.)

## Checking that everything works

Double-click **`check_system.bat`** for a one-screen report: Python, GPU (it runs a
real test — `cuda.is_available()` alone can lie when the CUDA build doesn't match the
card), the search model, loaded manuals, offline AI, OCR and updates. If something is
wrong it prints exactly what to do. Handy to send as a screenshot when asking for help.

## Updating

To push an update to another computer (e.g. the user's), keep the project in a (private)
git repository. The user runs **`update.bat`** — it fetches the latest code, refreshes
the libraries, and updates the local AI model. Personal data (manuals, `.env`, settings)
is git-ignored and left untouched. One-time setup on the user's machine: install
[git](https://git-scm.com/download/win) and `git clone` the repo once.

## Offline AI (local model, free)

The **"Offline AI"** search depth answers using a local model via **Ollama** instead of
Claude — free and fully offline (good at sea). Quality is lower than Claude, so it's the
no-cost / no-internet option; the online modes remain best for hard questions.

To enable it:
1. Install **Ollama** from https://ollama.com/download
2. Run `setup.bat` again — it downloads the model (`qwen2.5:7b`, ~5 GB, one-time).

`qwen2.5:7b` fits an 8 GB GPU (e.g. a laptop RTX 4060). Change the model in `config.py`
(`OLLAMA_MODEL`) — e.g. `qwen2.5:14b` on a 12 GB+ GPU for better quality. If Ollama isn't
running, the Offline AI mode simply shows the manual excerpts with a hint.

## Scanned manuals (OCR)

Many paper manuals are scanned — each page is an **image**, with no machine-readable
text. The app detects this automatically: when an uploaded PDF has little or no text, it
runs **OCR** (optical character recognition) to add a text layer, then indexes it. A
successful scan shows "(text recovered via OCR)" after upload.

OCR needs the free **Tesseract** engine installed on the system (the `ocrmypdf` Python
library is installed by `setup.bat`, but the engine is separate):

- **Windows:** install from https://github.com/UB-Mannheim/tesseract/wiki and make sure
  `tesseract` is on your PATH. Also install **Ghostscript** (https://www.ghostscript.com/).
- Set OCR languages in `.env` if needed: `OCR_LANGUAGES=eng` (or `eng+rus` for both).

If Tesseract isn't installed, text PDFs still work normally; scans are simply skipped
with a clear message.

## Daily spending

Every answer's real cost (from Claude's token usage) is added to a running **daily
total**, shown at the top of the page as `Today: ≈ $X · N question(s)`. The history is
kept in `usage_log.json`. This is informational only — to enforce a hard cap, set a
spend limit in the Anthropic Console (Settings → Limits).

## Token saving — document routing

To keep token use low, search is **two-stage**. At upload, each manual gets a compact
"map" (the average of its chunk vectors). At question time the app first picks the
1–2 most relevant manuals **locally and for free**, then retrieves chunks only from
those — fewer, more on-target chunks reach Claude (`TOP_K_ROUTED`, default 4, vs 6).
This cuts input tokens and improves precision, and matters more as the library grows.
It costs no extra Claude tokens (routing is done by the local model). If anything goes
wrong, routing silently falls back to searching all documents.

**Search depth (in the web UI):** a "Search depth" selector lets you balance
precision vs cost without editing any files — the choice is saved to `settings.json`
and applied immediately:

| Depth | Manuals searched | Excerpts sent | When to use |
|---|---|---|---|
| Economy | 1 | 3 | cheapest, quick lookups |
| Balanced | 2 | 4 | default |
| Thorough | 3 | 8 | hardest questions, best answers (costs more) |
| Offline AI | 2 | 6 | **uses the local model (Ollama), not Claude** — free, works with no internet. Quality is lower than Claude, so use it as the at-sea / no-cost option. If Ollama isn't installed, it falls back to showing excerpts only. |

(Defaults still live in `config.py`: `ROUTE_DOCS`, `ROUTE_TOP_DOCS`, `TOP_K_ROUTED`.)

## Limitations

- For scanned PDFs, OCR quality depends on scan clarity; very poor scans may extract
  imperfect text.
