"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

This implementation uses the OpenAI API (`pip install openai`, set
OPENAI_API_KEY). Keep the provider isolated here so the service can swap
providers without changing the cache or API routes.

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

from openai import AsyncOpenAI

MODEL_DEFAULT = os.getenv("MODEL", "gpt-5.6-luna")


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default)."""
    instructions = (
        "You are a professional translator. Translate the user's English text "
        "into natural Mexican Spanish (es-MX), using vocabulary and phrasing "
        "that would read naturally in Mexico. Return ONLY the translation: no "
        "preamble, no explanations, no markdown, and no wrapping quotes. "
        "Preserve all numbers, prices with $, measurements, URLs, product names, "
        "model codes, SKUs, and other alphanumeric identifiers exactly as written."
    )
    client = AsyncOpenAI()
    response = await client.responses.create(
        model=model,
        instructions=instructions,
        input=text,
        max_output_tokens=1024,
    )
    translated = response.output_text.strip()
    if (
        len(translated) >= 2
        and translated[0] == translated[-1]
        and translated[0] in {'"', "'"}
    ):
        translated = translated[1:-1].strip()
    return translated
