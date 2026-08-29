"""Answer assembly: find chunks in the manuals and ask Claude to answer with citations."""
import anthropic

import config
import costs
import local_llm
from search import search

SYSTEM_PROMPT = """You are a technical assistant for a ship's mechanic. You answer \
questions strictly from the provided excerpts of official manuals for marine parts \
and equipment.

Rules:
- Use ONLY the information in the provided excerpts. Do not invent or add anything \
from general knowledge.
- If the excerpts do not contain the answer, say so plainly: "The loaded manuals do \
not contain a precise answer to this question," and suggest which section/document \
to check.
- After every statement or step, add a source reference in the form [Source N].
- Answer clearly and concisely. For repair/replacement procedures, give a numbered \
list of steps.
- Include safety warnings whenever the manual states them.
"""


def _usage_cost(usage):
    """Turn Claude's token usage into a dollar cost for display."""
    price = config.PRICING.get(config.CLAUDE_MODEL, {"in": 5.0, "out": 25.0})
    in_tok = usage.input_tokens
    out_tok = usage.output_tokens
    cost = in_tok / 1e6 * price["in"] + out_tok / 1e6 * price["out"]
    return {
        "input": in_tok,
        "output": out_tok,
        "cost_usd": round(cost, 4),
        "model": config.CLAUDE_MODEL,
    }


def _build_user_prompt(question, results):
    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(
            f"[Source {i}] File: {r['source']}, page {r['page']}\n{r['text']}"
        )
    context = "\n\n---\n\n".join(blocks)
    return (
        f"Mechanic's question: {question}\n\n"
        f"Excerpts from the manuals:\n\n{context}\n\n"
        f"Answer the question using only these excerpts, with [Source N] references."
    )


def answer(question):
    """Main entry point: search + answer generation.
    Returns a dict with the answer, the sources, and an online flag."""
    results = search(question)

    if not results:
        return {
            "answer": "Nothing was found in the loaded manuals for this query. "
            "Make sure the relevant PDFs have been uploaded.",
            "sources": [],
            "online": None,
        }

    sources = [
        {
            "n": i + 1,
            "source": r["source"],
            "page": r["page"],
            "score": r["score"],
            "text": r["text"],
        }
        for i, r in enumerate(results)
    ]

    user_prompt = _build_user_prompt(question, results)

    # Offline depth -> the local model. Free, no internet, nothing billed.
    if config.AI_BACKEND == "local":
        if local_llm.is_available():
            try:
                text = local_llm.generate(SYSTEM_PROMPT, user_prompt)
                if not text:
                    raise ValueError("empty response from local model")
                return {"answer": text, "sources": sources, "online": False,
                        "engine": "local"}
            except Exception as e:
                return {
                    "answer": None,
                    "sources": sources,
                    "online": False,
                    "note": f"Local AI error ({type(e).__name__}). Showing manual excerpts.",
                }
        return {
            "answer": None,
            "sources": sources,
            "online": False,
            "note": "Local AI (Ollama) is not running or the model isn't installed. "
            "Install Ollama and run setup again, or pick an online mode. "
            "Showing manual excerpts for now.",
        }

    # No key -> show the retrieved excerpts without a Claude answer.
    if not config.ANTHROPIC_API_KEY:
        return {
            "answer": None,
            "sources": sources,
            "online": False,
            "note": "No ANTHROPIC_API_KEY set — AI answer unavailable. "
            "Below are the manual excerpts found for your question.",
        }

    try:
        client = anthropic.Anthropic()
        kwargs = dict(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if config.USE_THINKING:
            kwargs["thinking"] = {"type": "adaptive"}

        resp = client.messages.create(**kwargs)
        usage = _usage_cost(resp.usage)
        # tokens were billed whether or not we got text back — record the spend
        costs.record(usage["cost_usd"], usage["input"], usage["output"])
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not text:
            # Rare: the whole budget went to thinking / hit the token cap.
            return {
                "answer": None,
                "sources": sources,
                "online": True,
                "usage": usage,
                "note": "The answer came back empty (likely hit the token limit). "
                "Try a more specific question, or raise CLAUDE_MAX_TOKENS in config.py.",
            }
        return {
            "answer": text,
            "sources": sources,
            "online": True,
            "usage": usage,
        }

    except Exception as e:
        # Most likely no internet (at sea). Don't fail — return the excerpts.
        return {
            "answer": None,
            "sources": sources,
            "online": False,
            "note": f"Could not reach Claude ({type(e).__name__}). "
            "There may be no internet connection. Below are the manual excerpts found.",
        }
