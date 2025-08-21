from __future__ import annotations
import os, io, base64, time, random
from pathlib import Path
from typing import Optional, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from langdetect import detect, DetectorFactory
from gtts import gTTS
from gtts.lang import tts_langs

from genai import generate_text  

# ---------- env ----------
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

app = FastAPI(title="Voygan – Tourism Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR     = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
HTML_DIR     = FRONTEND_DIR / "html"
STATIC_DIR   = FRONTEND_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse(HTML_DIR / "index.html")


class ChatRequest(BaseModel):
    message: str
    place: Optional[str] = None
    tts: bool = True

class ChatResponse(BaseModel):
    bot_name: str
    language: str
    text: str
    audio_b64: Optional[str] = None
    audio_mime: Optional[str] = None
    detected_place: Optional[str] = None
    tts_ms: Optional[int] = None


BOT_NAME = "Voygan"

WELCOME_MESSAGES = [
    "Hello! Welcome to Voyagen, your travel companion! How can I assist you today?",
    "Greetings! So glad you're here with Voyagen. What is on your travel mind?",
    "Hey there! Voyagen is excited to guide you. Where would you like to go?",
    "Warm welcome to Voyagen! I’m here to help you explore. What is your plan?",
    "Hi! You have arrived at Voyagen, your travel buddy. How can I help you today?",
]
_last_welcome_idx = -1
def random_welcome() -> str:
    global _last_welcome_idx
    if not WELCOME_MESSAGES: return "Hello!"
    idx = random.randrange(len(WELCOME_MESSAGES))
    if len(WELCOME_MESSAGES) > 1 and idx == _last_welcome_idx:
        idx = (idx + 1) % len(WELCOME_MESSAGES)
    _last_welcome_idx = idx
    return WELCOME_MESSAGES[idx]


DetectorFactory.seed = 42

_TTS_ALL: Dict[str, str] = {k.lower(): v for k, v in tts_langs().items()}

_GEMINI_SAFE = {
    # Africa / Middle East / South Asia
    "af","ar","bn","gu","hi","mr","ml","ta","te","ur","sw",
    # Europe
    "bs","ca","cs","cy","da","de","el","en","es","et","fi","fr","hr","hu",
    "is","it","lv","mk","nl","no","pl","pt","ro","ru","sk","sq","sr","sv","tr","uk",
    # East / SE Asia
    "id","ja","jw","jv","km","kn","ko","my","ne","si","th","vi",
    # Extras present in gTTS
    "eo","la","su","pt",
    # Chinese variants (normalize below)
    "zh","zh-cn","zh-tw",
}

def _normalize(code: str) -> str:
    """Normalize detector codes to our public codes."""
    c = (code or "en").lower().replace("_", "-")
 
    if c.startswith("zh"):
        return "zh-tw" if ("tw" in c or "hant" in c) else "zh-cn"
    if c in ("jv", "jw"):
        return "jv"
    if c.startswith("pt-"):
        return "pt"
    return c

def _tts_code(public_code: str) -> str:
    if public_code == "jv":
        return "jw" if "jw" in _TTS_ALL else "jv"
    if public_code == "zh-cn":
        return "zh-cn" if "zh-cn" in _TTS_ALL else ("zh" if "zh" in _TTS_ALL else "zh-cn")
    if public_code == "zh-tw":
        return "zh-tw" if "zh-tw" in _TTS_ALL else ("zh" if "zh" in _TTS_ALL else "zh-tw")
    return public_code


SUPPORTED: set[str] = set()
for code in _GEMINI_SAFE:
    pub = _normalize(code)
    tts = _tts_code(pub)
    if tts in _TTS_ALL or pub in _TTS_ALL:
        SUPPORTED.add(pub)


LANG_NAMES: Dict[str, str] = {}
for pub in SUPPORTED:
    tts = _tts_code(pub)
    name = _TTS_ALL.get(tts, pub)
    if pub == "zh-cn": name = "Chinese (Simplified)"
    if pub == "zh-tw": name = "Chinese (Traditional)"
    if pub == "jv":    name = "Javanese"
    LANG_NAMES[pub] = name

def supported_languages() -> Dict[str, str]:
    return dict(sorted(LANG_NAMES.items(), key=lambda kv: kv[1].lower()))

def choose_target_language(user_text: str) -> str:
    """Detect user's language → if unsupported, fall back to 'en'."""
    try:
        detected = detect(user_text)
    except Exception:
        return "en"
    lang = _normalize(detected)
    return lang if lang in SUPPORTED else "en"


def tts_to_base64(text: str, lang_code: str) -> tuple[str, str, int]:
    """Return (audio_b64, mime, elapsed_ms)."""
    t0 = time.time()
    buf = io.BytesIO()
    gTTS(text=text, lang=_tts_code(lang_code)).write_to_fp(buf)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    ms = int((time.time() - t0) * 1000)
    return b64, "audio/mpeg", ms



@app.get("/api/supported-languages")
def api_supported_languages():
    """Handy for your app to know what's enabled."""
    return supported_languages()

@app.get("/api/greet", response_model=ChatResponse)
def greet():
    # Text-only welcome (NO TTS for the first message)
    return ChatResponse(
        bot_name=BOT_NAME,
        language="en",
        text=random_welcome()
    )

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # Detect & clamp to supported languages (fallback to English)
    lang = choose_target_language(req.message)

    try:
        text = generate_text(user_lang=lang, message=req.message, place=req.place)
        if not text:
            raise RuntimeError("Empty model output")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {e}")

    audio_b64 = audio_mime = None
    tts_ms = None
    if req.tts:
        try:
            audio_b64, audio_mime, tts_ms = tts_to_base64(text, lang)
        except Exception:
            # Keep text even if TTS fails
            pass

    return ChatResponse(
        bot_name=BOT_NAME,
        language=lang,  
        text=text,
        audio_b64=audio_b64,
        audio_mime=audio_mime,
        detected_place=req.place,
        tts_ms=tts_ms
    )

@app.get("/api/health")
def health():
    return {"ok": True, "languages_supported": len(SUPPORTED)}