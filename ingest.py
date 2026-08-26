"""Load PDFs into the vector database: PDF -> text -> chunks -> vectors -> Chroma."""
import tempfile
from pathlib import Path
import chromadb
import numpy as np

import config
import ocr
from chunking import extract_pages, build_chunks
from embeddings import embed_passages

try:
    from chromadb.errors import InvalidDimensionException
except Exception:  # keep working across chromadb versions
    InvalidDimensionException = Exception

_client = None
_collection = None
_doc_maps = None


class IndexModelMismatch(Exception):
    """Raised when the saved index was built with a different embedding model."""


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(config.DB_DIR))
    return _client


def get_collection():
    """Local Chroma vector database (stored on disk, works offline).
    The collection records which embedding model built it, so we can detect a mismatch."""
    global _collection
    if _collection is None:
        _collection = _get_client().get_or_create_collection(
            config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": config.EMBEDDING_MODEL},
        )
    return _collection


def get_doc_maps():
    """One vector per document (centroid of its chunks). Used to route a question to
    the most relevant manual(s) before searching — saves tokens, improves precision."""
    global _doc_maps
    if _doc_maps is None:
        _doc_maps = _get_client().get_or_create_collection(
            config.DOC_MAPS_COLLECTION, metadata={"hnsw:space": "cosine"}
        )
    return _doc_maps


def index_status():
    """Check whether the existing index is compatible with the current model.
    Cheap — does NOT load the embedding model."""
    col = get_collection()
    count = col.count()
    stored = (col.metadata or {}).get("embedding_model")
    current = config.EMBEDDING_MODEL
    # An empty index is always fine; a populated one must match the recorded model.
    compatible = not (count > 0 and stored is not None and stored != current)
    return {
        "count": count,
        "stored_model": stored,
        "current_model": current,
        "compatible": compatible,
    }


def reindex_all():
    """Wipe the index and rebuild it from every PDF in manuals/ using the current model.
    PDFs are already saved on disk, so nothing needs to be re-uploaded."""
    reset_all()
    results = []
    for pdf in sorted(config.MANUALS_DIR.glob("*.pdf")):
        results.append(ingest_pdf(pdf, source_name=pdf.name))
    return results


def ingest_pdf(pdf_path, source_name=None):
    """Index one PDF. If the file was loaded before, re-index it from scratch."""
    source = source_name or Path(pdf_path).name
    col = get_collection()

    # remove old chunks of this same file (avoid duplicates on re-indexing)
    try:
        col.delete(where={"source": source})
    except Exception:
        pass

    pages = extract_pages(pdf_path)
    ocr_used = False

    # If this looks like a scan (little/no extractable text), try OCR.
    if ocr.should_ocr(pages):
        if ocr.is_available():
            ocr_pdf = Path(tempfile.gettempdir()) / f"ocr_{source}"
            try:
                ocr.run_ocr(pdf_path, ocr_pdf)
                pages = extract_pages(ocr_pdf)
                ocr_used = True
            except Exception as e:
                return {
                    "source": source,
                    "chunks": 0,
                    "warning": f"This is a scan and OCR failed ({type(e).__name__}). "
                    "Check that the PDF is valid.",
                }
            finally:
                if ocr_pdf.exists():
                    try:
                        ocr_pdf.unlink()
                    except Exception:
                        pass
        else:
            return {
                "source": source,
                "chunks": 0,
                "warning": "This is a scan with no text layer, and the Tesseract OCR "
                "engine is not installed. Install Tesseract to index scanned manuals.",
            }

    chunks = build_chunks(pages, source, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    if not chunks:
        return {
            "source": source,
            "chunks": 0,
            "warning": "Could not extract any text from this PDF, even after OCR.",
        }

    texts = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "page": c["page"]} for c in chunks]
    ids = [f"{source}::{i}" for i in range(len(chunks))]

    # compute vectors and add in batches (so large manuals don't blow up memory)
    batch = 256
    centroid_sum = None
    total_n = 0
    try:
        for start in range(0, len(chunks), batch):
            sl = slice(start, start + batch)
            embeddings = embed_passages(texts[sl])
            arr = np.asarray(embeddings, dtype="float32")
            centroid_sum = arr.sum(axis=0) if centroid_sum is None else centroid_sum + arr.sum(axis=0)
            total_n += arr.shape[0]
            col.add(
                ids=ids[sl],
                embeddings=embeddings,
                documents=texts[sl],
                metadatas=metadatas[sl],
            )
    except InvalidDimensionException:
        raise IndexModelMismatch(
            "The existing index was built with a different embedding model. "
            "Re-index to rebuild it with the current model."
        )

    # store this document's "map" (centroid of its chunks) for query routing
    if total_n and centroid_sum is not None:
        centroid = centroid_sum / total_n
        norm = float(np.linalg.norm(centroid))
        if norm > 0:
            centroid = centroid / norm
        get_doc_maps().upsert(
            ids=[source],
            embeddings=[centroid.tolist()],
            metadatas=[{"source": source}],
        )

    return {"source": source, "chunks": len(chunks), "ocr_used": ocr_used}


def list_sources():
    """List of loaded manuals and how many chunks each has."""
    col = get_collection()
    total = col.count()
    if total == 0:
        return [], 0
    data = col.get(include=["metadatas"])
    counts = {}
    for meta in data["metadatas"]:
        counts[meta["source"]] = counts.get(meta["source"], 0) + 1
    sources = [{"source": s, "chunks": n} for s, n in sorted(counts.items())]
    return sources, total


def delete_source(source):
    get_collection().delete(where={"source": source})
    try:
        get_doc_maps().delete(ids=[source])
    except Exception:
        pass


def reset_all():
    """Wipe the database completely (chunks + document maps)."""
    client = _get_client()
    for name in (config.COLLECTION_NAME, config.DOC_MAPS_COLLECTION):
        try:
            client.delete_collection(name)
        except Exception:
            pass
    global _collection, _doc_maps
    _collection = None
    _doc_maps = None
