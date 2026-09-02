"""Free-form writing helper that runs on the LOCAL model: translate text in either
direction, rewrite it, or format it as a letter/email. Free, works with no internet.

Separate from the manual Q&A: there is no document retrieval here, the user's own
text is the whole input.
"""
import config
import local_llm

# What to do when the user just pastes text without naming a language.
DIRECTIONS = {
    # Two-way: pick the target from the language the text is written in.
    "auto": "If the text is mainly Russian, translate it into English. "
            "If the text is in English or any other language, translate it into "
            "Russian. Never return the text in the same language it came in.",
    "en": "Translate the text into English.",
    "ru": "Translate the text into Russian.",
}
DEFAULT_DIRECTION = "auto"

SYSTEM_PROMPT = """You are a writing assistant for a ship's mechanic. The user gives \
you some text, sometimes with an instruction. The instruction may be written in \
Russian or English; the text may be in any language.

Do exactly what the instruction asks - translate, rewrite, correct, shorten, or format \
the text.

Rules:
- Output ONLY the finished result. No preamble, no explanation of what you did, no \
notes, no comments about the translation.
- If asked for a letter or an email, format it properly (greeting, body, sign-off).
- Keep technical and marine terminology accurate; do not invent facts or add content \
the user did not provide.
- Preserve numbers, part codes and units exactly as given.
- If the user's instruction names a target language, follow the instruction.
- Otherwise apply this rule: {direction}
"""


def is_available():
    return local_llm.is_available()


def translate(request_text, direction=DEFAULT_DIRECTION):
    """Run the user's request through the local model. Returns the finished text.
    `direction` decides the target language when the user didn't name one:
    'auto' translates Russian->English and anything else->Russian.
    Raises on failure so the caller can show a clear message."""
    text = (request_text or "").strip()
    if not text:
        raise ValueError("empty request")
    if direction not in DIRECTIONS:
        raise ValueError(f"unknown direction: {direction}")

    result = local_llm.generate(
        SYSTEM_PROMPT.format(direction=DIRECTIONS[direction]),
        text,
        concise=False,                       # length should follow the request
        max_tokens=config.TRANSLATE_MAX_TOKENS,
    )
    if not result:
        raise ValueError("the model returned nothing")
    return result
