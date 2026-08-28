"""Big local model via FreeToken (optional, offline, free).

FreeToken runs frontier MoE models on consumer hardware by spreading them across
GPU + system RAM. It serves an Anthropic-compatible API, so we talk to it with the
same SDK we use for Claude - just pointed at localhost.

Everything here is best-effort: if FreeToken isn't installed or running, callers
fall back to the small local model or to manual excerpts. Start it with:
    ft serve <model>
"""
import json
import urllib.request

import config

# Discovered server base URL is cached here after the first successful probe.
_base_url = None
_model_id = None


def _probe(base):
    """Return the list of model ids served at `base`, or None if nothing answers."""
    try:
        req = urllib.request.Request(base.rstrip("/") + "/v1/models")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    # OpenAI-style: {"data": [{"id": "..."}, ...]}
    models = [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
    return [m for m in models if m]


def discover():
    """Find a running FreeToken server and the model it serves.
    The port isn't fixed by the project, so try the configured URL first, then
    the usual suspects. Returns (base_url, model_id) or (None, None)."""
    global _base_url, _model_id
    if _base_url and _model_id:
        return _base_url, _model_id

    candidates = [config.FREETOKEN_URL] + [
        u for u in config.FREETOKEN_FALLBACK_URLS if u != config.FREETOKEN_URL
    ]
    for base in candidates:
        models = _probe(base)
        if not models:
            continue
        # Prefer the configured model when it is actually served; otherwise take
        # whatever is loaded, so the user never has to match name strings.
        want = config.FREETOKEN_MODEL
        chosen = want if want and want in models else models[0]
        _base_url, _model_id = base, chosen
        return _base_url, _model_id
    return None, None


def is_available():
    base, model = discover()
    return bool(base and model)


def describe():
    """Short human-readable status, for the system check."""
    base, model = discover()
    return f"{model} at {base}" if base else ""


def generate(system, prompt):
    """Generate an answer with the big local model. Raises on failure."""
    import anthropic

    base, model = discover()
    if not base:
        raise RuntimeError("FreeToken server not found")

    # FreeToken exposes an Anthropic-compatible /v1/messages endpoint. No real key
    # is needed locally, but the SDK requires the field to be set.
    client = anthropic.Anthropic(base_url=base, api_key="local", timeout=600.0)
    resp = client.messages.create(
        model=model,
        max_tokens=config.FREETOKEN_MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
