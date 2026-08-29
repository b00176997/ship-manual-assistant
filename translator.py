"""Free-form writing helper that runs on the LOCAL model: translate text, rewrite
it, or format it as a letter/email. Free, works with no internet.

Separate from the manual Q&A: there is no document retrieval here, the user's own
text is the whole input.
"""
import config
import local_llm

SYSTEM_PROMPT = """You are a writing assistant for a ship's mechanic. The user gives \
you an instruction together with some text. The instruction may be written in Russian \
or English; the text may be in any language.

Do exactly what the instruction asks - translate, rewrite, correct, shorten, or format \
the text.

Rules:
- Output ONLY the finished result. No preamble, no explanation of what you did, no \
notes, no comments about the translation.
- If asked for a letter or an email, format it properly (greeting, body, sign-off).
- Keep technical and marine terminology accurate; do not invent facts or add content \
the user did not provide.
- Preserve numbers, part codes and units exactly as given.
- If the instruction does not name a target language, translate into English.
"""


def is_available():
    return local_llm.is_available()


def translate(request_text):
    """Run the user's request through the local model. Returns the finished text.
    Raises on failure so the caller can show a clear message."""
    text = (request_text or "").strip()
    if not text:
        raise ValueError("empty request")

    result = local_llm.generate(
        SYSTEM_PROMPT,
        text,
        concise=False,                       # length should follow the request
        max_tokens=config.TRANSLATE_MAX_TOKENS,
    )
    if not result:
        raise ValueError("the model returned nothing")
    return result
