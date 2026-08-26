"""Local model that turns text into vectors (runs offline, uses GPU if available)."""
import config

_model = None


def _pick_device():
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def get_model():
    """Load the model once (this is the heavy step)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        device = _pick_device()
        print(f"[embeddings] Loading model {config.EMBEDDING_MODEL} on {device.upper()} ...")
        _model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
        print("[embeddings] Model ready.")
    return _model


def _batch_size(model):
    # bigger batches are faster on a GPU; modest on CPU to keep RAM in check
    return 64 if str(model.device).startswith("cuda") else 16


def embed_passages(texts):
    """Vectors for document chunks."""
    model = get_model()
    inputs = [f"{config.PASSAGE_PREFIX}{t}" for t in texts]
    vectors = model.encode(
        inputs,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=_batch_size(model),
    )
    return vectors.tolist()


def embed_query(text):
    """Vector for a user's question."""
    model = get_model()
    vector = model.encode(f"{config.QUERY_PREFIX}{text}", normalize_embeddings=True)
    return vector.tolist()
