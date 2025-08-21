from __future__ import annotations
import os, re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load env from project root
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel(MODEL_NAME)

# Keep output short & snappy
GEN_CFG = {
    "temperature": 0.4,
    "max_output_tokens": 320,
}

SYSTEM = """
You are Voygan, a multilingual tourism guide.

OUTPUT FORMAT (very important):
Return EXACTLY FIVE PARAGRAPHS, in this order:
1) About the place (what/where/why famous)
2) Who built or founded it (if applicable; otherwise say it's unknown/not applicable)
3) How many buildings/sections/levels (if meaningful; otherwise say briefly that it doesn’t apply)
4) Famous local foods or souvenirs
5) Common local beliefs or customs (or state none if not applicable)

Rules:
- Write in the user's language.
- 2–4 concise sentences per paragraph.
- No headings, labels, bullets, numbering, JSON, or extra text before/after.
- Just the five paragraphs separated by blank lines.
"""

def _clean(text: str) -> str:
    """Strip accidental code fences or labels the model might add."""
    t = text.strip()
    # remove ``` or ```json fences if present
    t = re.sub(r"^\s*```(?:\w+)?\s*", "", t)
    t = re.sub(r"\s*```\s*$", "", t)
    # Some models add leading labels like "about:"—remove common ones at paragraph starts
    t = re.sub(r"(?mi)^(about|builder[_\s-]*founder|sections[_\s-]*buildings|food[_\s-]*souvenir|beliefs[_\s-]*customs)\s*:\s*", "", t)
    return t.strip()

def _build_prompt(user_lang: str, message: str, place: str | None) -> str:
    focus = f"Place focus: {place}\n" if place else ""
    return (
        f"{SYSTEM}\n"
        f"User language code: {user_lang}\n"
        f"{focus}"
        f'User message: """{message}"""\n'
        "Respond with the five paragraphs only."
    )

def generate_text(user_lang: str, message: str, place: str | None) -> str:
    """
    Returns a single string with five paragraphs (blank line between each).
    """
    prompt = _build_prompt(user_lang, message, place)
    out = MODEL.generate_content(prompt, generation_config=GEN_CFG)
    text = (out.text or "").strip()
    return _clean(text)
