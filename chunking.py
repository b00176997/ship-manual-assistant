"""PDF text extraction and chunking into semantic pieces with page tracking."""
import re
from pathlib import Path
from pypdf import PdfReader


def _clean(text):
    # collapse extra spaces/breaks but keep paragraph structure
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages(pdf_path):
    """Returns a list of (page_number, page_text)."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append((i + 1, _clean(text)))
    return pages


def _page_for_offset(offset, page_starts):
    """Given an offset in the full text, find which page it falls on."""
    page = page_starts[0][1]
    for start_offset, page_no in page_starts:
        if start_offset <= offset:
            page = page_no
        else:
            break
    return page


def build_chunks(pages, source, size, overlap):
    """Join pages into one text and cut with a sliding window.
    Each chunk remembers the page it started on — used for citations."""
    full = ""
    page_starts = []  # (offset_in_text, page_number)
    for page_no, text in pages:
        if not text:
            continue
        page_starts.append((len(full), page_no))
        full += text + "\n\n"

    if not full.strip():
        return []

    chunks = []
    step = max(1, size - overlap)
    i = 0
    while i < len(full):
        window = full[i:i + size].strip()
        if window:
            page = _page_for_offset(i, page_starts)
            chunks.append({"text": window, "source": source, "page": page})
        i += step
    return chunks
