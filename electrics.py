"""Photo-based help with the ship's electrical system.

The mechanic photographs a schematic or a panel, describes the problem, and gets
a structured diagnosis. Unlike the manual Q&A this is a CONVERSATION: fault
finding goes step by step ("measure X" -> "I read 0 V" -> next step), so the
history is kept per conversation and sent back with every turn.

Uses Claude (vision). Relevant manual excerpts are attached when the loaded
manuals actually cover the question.
"""
import base64
import io
import time
import uuid

import anthropic

import config
import costs
from search import search

SYSTEM_PROMPT = """You are helping a ship's mechanic work on the vessel's electrical \
system. He is a competent mechanic but NOT an electrician, so be concrete and never \
assume he will fill in gaps himself.

SAFETY - this comes before everything else:
- Before any hands-on step: isolate the circuit, lock it out, and VERIFY it is dead \
with a meter. Say this explicitly the first time you propose touching anything.
- Never propose working on live equipment. If a measurement genuinely requires the \
circuit energised, say so plainly, state the voltage involved, and tell him to treat \
it as live work with the ship's own permit/procedure.
- Flag stored energy (capacitors, UPS, batteries) and back-feed from other sources \
when they apply.
- Your answer is advice, not an instruction. Ship procedures and his own judgement \
come first.

READING THE PHOTO - be honest:
- Say what you can actually read and what you cannot. If a designation, terminal \
number or wire is blurred, cropped or ambiguous, SAY SO and ask for a closer photo.
- Never invent a component label, terminal number or wire colour. A confident wrong \
number is worse than "I can't read this".
- If the photo is too poor to work from at all, say that first and ask for a better one.

HOW TO ANSWER:
1. What you see: the components and the circuit involved, in plain words.
2. Most likely causes, ordered by how likely and how easy they are to check.
3. A numbered measurement plan: where to put the probes, what to expect, and what \
each result would mean. Ask him to report the readings back.
4. Only name a definite fault once measurements support it.

Keep it practical and short. Answer in the same language the mechanic writes in \
(he usually writes Russian). Use the manual excerpts when they are relevant, citing \
them as [Source N]; ignore them when they are not about this question."""

# Conversations live in memory: this is a single-user local app, and a diagnosis
# lasts minutes. Restarting the program simply starts a fresh conversation.
_conversations = {}
MAX_TURNS = 24          # keep a session from growing without bound
MAX_CONVERSATIONS = 20  # abandoned conversations must not leak memory
IMAGE_MAX_PX = 1600     # long edge; enough for schematic text, keeps cost sane
IMAGE_MIN_SCORE = 0.35  # below this the manuals clearly aren't about the question


def _shrink(raw_bytes, media_type):
    """Downscale a phone photo so it stays cheap and within API limits.
    Returns (base64_str, media_type). Falls back to the original on any problem."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw_bytes))
        img.load()
        if max(img.size) > IMAGE_MAX_PX:
            ratio = IMAGE_MAX_PX / max(img.size)
            img = img.resize((max(1, int(img.width * ratio)),
                              max(1, int(img.height * ratio))), Image.LANCZOS)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88, optimize=True)
        return base64.standard_b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"
    except Exception:
        return base64.standard_b64encode(raw_bytes).decode("ascii"), media_type


def _manual_context(question):
    """Excerpts from the loaded manuals, but only when they look relevant."""
    try:
        hits = search(question)
    except Exception:
        return "", []
    hits = [h for h in hits if h["score"] >= IMAGE_MIN_SCORE]
    if not hits:
        return "", []
    blocks = [f"[Source {i}] {h['source']}, page {h['page']}\n{h['text']}"
              for i, h in enumerate(hits, 1)]
    text = ("\n\nExcerpts from the ship's manuals that may or may not be relevant:\n\n"
            + "\n\n---\n\n".join(blocks))
    sources = [{"n": i, "source": h["source"], "page": h["page"],
                "score": h["score"], "text": h["text"]}
               for i, h in enumerate(hits, 1)]
    return text, sources


def start():
    """Create an empty conversation and return its id."""
    # Conversations hold photos, so don't let abandoned ones pile up in memory.
    if len(_conversations) >= MAX_CONVERSATIONS:
        oldest = sorted(_conversations, key=lambda k: _conversations[k]["created"])
        for k in oldest[:len(_conversations) - MAX_CONVERSATIONS + 1]:
            _conversations.pop(k, None)
    cid = uuid.uuid4().hex
    _conversations[cid] = {"messages": [], "created": time.time()}
    return cid


def reset(conv_id):
    _conversations.pop(conv_id, None)


def ask(conv_id, question, images=None):
    """One turn. `images` is a list of (raw_bytes, media_type) for this turn only.
    Returns dict with the answer, any manual sources used, usage and conv_id."""
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "No API key set, so photo diagnosis is unavailable. This feature needs "
            "the internet - it cannot run on the local model."
        )
    question = (question or "").strip()
    if not question and not images:
        raise ValueError("nothing to work with: add a photo or describe the problem")

    conv = _conversations.get(conv_id)
    if conv is None:
        conv_id = start()
        conv = _conversations[conv_id]

    content = []
    for raw, media_type in (images or []):
        data, mt = _shrink(raw, media_type)
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": mt, "data": data}})

    manual_text, sources = _manual_context(question) if question else ("", [])
    content.append({"type": "text", "text": (question or "See the photo.") + manual_text})

    conv["messages"].append({"role": "user", "content": content})
    # Trim the oldest turns rather than letting an old photo inflate every request.
    # Slicing alone is not enough: the API requires the history to START with a
    # user message, and a plain tail slice can begin with an assistant reply.
    if len(conv["messages"]) > MAX_TURNS:
        trimmed = conv["messages"][-MAX_TURNS:]
        while trimmed and trimmed[0]["role"] != "user":
            trimmed.pop(0)
        conv["messages"] = trimmed

    client = anthropic.Anthropic()
    # A diagnosis runs several turns and the API is stateless, so the photo is
    # re-sent every time. Caching the conversation prefix makes those repeats
    # cost about a tenth as much.
    resp = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.ELECTRICS_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=conv["messages"],
        cache_control={"type": "ephemeral"},
    )
    answer = "".join(b.text for b in resp.content if b.type == "text").strip()
    conv["messages"].append({"role": "assistant", "content": answer or "(no answer)"})

    # With caching on, input tokens are split across three counters and each is
    # billed at a different rate. Counting only `input_tokens` would report a
    # cost far below what was actually charged.
    price = config.PRICING.get(config.CLAUDE_MODEL, {"in": 3.0, "out": 15.0})
    u = resp.usage
    fresh = u.input_tokens
    written = getattr(u, "cache_creation_input_tokens", 0) or 0   # ~1.25x
    read = getattr(u, "cache_read_input_tokens", 0) or 0          # ~0.1x
    cost = (fresh / 1e6 * price["in"]
            + written / 1e6 * price["in"] * 1.25
            + read / 1e6 * price["in"] * 0.1
            + u.output_tokens / 1e6 * price["out"])
    total_in = fresh + written + read
    costs.record(round(cost, 6), total_in, u.output_tokens)

    return {
        "conv_id": conv_id,
        "answer": answer,
        "sources": sources,
        "usage": {"input": total_in, "output": u.output_tokens, "cached": read,
                  "cost_usd": round(cost, 4), "model": config.CLAUDE_MODEL},
        "turns": len([m for m in conv["messages"] if m["role"] == "user"]),
    }
