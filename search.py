"""Semantic search: question -> vector -> nearest chunks.
Two-stage when ROUTE_DOCS is on: first pick the most relevant manual(s) locally
(free), then search only inside them — fewer tokens, better precision. Works offline."""
import config
from embeddings import embed_query
from ingest import (
    get_collection,
    get_doc_maps,
    IndexModelMismatch,
    InvalidDimensionException,
)


def _route(q_vec):
    """Pick the most relevant document(s) for this query. Best-effort: any problem
    just disables routing (search falls back to all documents)."""
    if not config.ROUTE_DOCS:
        return None
    try:
        dm = get_doc_maps()
        if dm.count() == 0:
            return None
        rr = dm.query(
            query_embeddings=[q_vec],
            n_results=min(config.ROUTE_TOP_DOCS, dm.count()),
            include=["metadatas"],
        )
        docs = [m["source"] for m in rr["metadatas"][0]]
        return docs or None
    except Exception:
        return None


def _format(res):
    out = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        out.append(
            {
                "text": doc,
                "source": meta["source"],
                "page": meta["page"],
                "score": round(1 - dist, 3),  # cosine: closer to 1 = more relevant
            }
        )
    return out


def search(question, top_k=None):
    """Returns the most relevant manual chunks. Works offline."""
    col = get_collection()
    if col.count() == 0:
        return []

    q_vec = embed_query(question)
    routed_docs = _route(q_vec)

    where = {"source": {"$in": routed_docs}} if routed_docs else None
    k = top_k or (config.TOP_K_ROUTED if routed_docs else config.TOP_K)

    try:
        res = col.query(
            query_embeddings=[q_vec],
            n_results=min(k, col.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except InvalidDimensionException:
        raise IndexModelMismatch(
            "The existing index was built with a different embedding model. "
            "Re-index to rebuild it with the current model."
        )

    # Safety net: if routing filtered everything out, search globally instead.
    if where is not None and not res["documents"][0]:
        res = col.query(
            query_embeddings=[q_vec],
            n_results=min(config.TOP_K, col.count()),
            include=["documents", "metadatas", "distances"],
        )

    return _format(res)
