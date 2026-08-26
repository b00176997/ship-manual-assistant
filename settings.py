"""Runtime-adjustable settings, changeable from the web UI and saved to disk.
Currently: 'search depth' — the precision vs token-cost tradeoff. Changing it
overrides the routing parameters in config live (and persists across restarts)."""
import json
import config

SETTINGS_FILE = config.BASE_DIR / "settings.json"

# Each depth maps to concrete retrieval parameters and an answer backend.
# More docs + more chunks = more thorough answers but more tokens.
# "offline" uses the local model (Ollama): free, no internet — backend="local".
DEPTH_PRESETS = {
    "offline":  {"ROUTE_TOP_DOCS": 2, "TOP_K_ROUTED": 6, "backend": "local"},
    "economy":  {"ROUTE_TOP_DOCS": 1, "TOP_K_ROUTED": 3, "backend": "claude"},
    "balanced": {"ROUTE_TOP_DOCS": 2, "TOP_K_ROUTED": 4, "backend": "claude"},
    "thorough": {"ROUTE_TOP_DOCS": 3, "TOP_K_ROUTED": 8, "backend": "claude"},
}
DEFAULT_DEPTH = "balanced"

_depth = DEFAULT_DEPTH


def _apply(depth):
    preset = DEPTH_PRESETS[depth]
    config.ROUTE_TOP_DOCS = preset["ROUTE_TOP_DOCS"]
    config.TOP_K_ROUTED = preset["TOP_K_ROUTED"]
    config.AI_BACKEND = preset["backend"]


def load_and_apply():
    """Read the saved depth (if any) and apply it to the live config."""
    global _depth
    depth = DEFAULT_DEPTH
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if data.get("depth") in DEPTH_PRESETS:
                depth = data["depth"]
        except Exception:
            pass
    _depth = depth
    _apply(depth)
    return depth


def get_depth():
    return _depth


def set_depth(depth):
    """Validate, apply, and persist a new search depth. Returns the applied depth."""
    global _depth
    if depth not in DEPTH_PRESETS:
        raise ValueError(f"Unknown search depth: {depth}")
    _depth = depth
    _apply(depth)
    try:
        SETTINGS_FILE.write_text(
            json.dumps({"depth": depth}, indent=2), encoding="utf-8"
        )
    except Exception:
        pass
    return depth
