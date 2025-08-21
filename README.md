# Voygan — Tourism Chatbot

Voygan is a multilingual tourism chatbot built with FastAPI, Gemini (Google Generative AI), and gTTS. Users can ask about a place or monument, and the bot responds in the user’s language with five concise paragraphs covering:

1. About the place
2. Who built or founded it (if applicable)
3. Buildings, sections, or levels (if meaningful)
4. Famous local foods or souvenirs
5. Common local beliefs or customs (or “none/not applicable”)

Responses include optional voice narration returned as base64-encoded MP3 audio.

## Features
- **FastAPI backend**: Lightweight and fast API framework
- **Gemini integration**: Uses Google Generative AI for text generation (model configurable via `.env`)
- **gTTS for speech**: Supports text-to-speech in multiple languages
- **Language auto-detection**: Falls back to English if the user’s language is unsupported
- **Random welcome message**: Text-only greeting on `/api/greet`
- **Simple test UI**: Served from the backend (optional, can be removed for API-only use)
- **Dynamic language support**: Lists supported languages at runtime via `/api/supported-languages`

## Project Structure
```
voygan/
├─ frontend/
│  ├─ html/
│  │  └─ index.html         # Simple test UI (Tailwind + vanilla JS)
│  └─ static/
│     ├─ style.css          # UI styles
│     └─ script.js          # UI logic
├─ genai.py                 # Gemini wrapper (enforces 5-paragraph format)
├─ main.py                  # FastAPI app (routing, TTS, language logic)
├─ requirements.txt         # Python dependencies
└─ .env.example             # Sample env file (copy to .env)
```

## Prerequisites
- Python 3.9+
- Google AI Studio API key (for Gemini)
- Internet access (required for gTTS)

## Setup
1. Clone the repository or place the project folder, then create a virtual environment:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your `.env` file from the example and add your API key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   GEMINI_API_KEY=YOUR_KEY
   GEMINI_MODEL=gemini-1.5-flash   # or gemini-1.5-flash-8b

   TTS_PROVIDER=gtts
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

5. Open `http://127.0.0.1:8000` in your browser to access the test UI. API endpoints are available under `/api/*`.

## Environment Variables
Create a `.env` file in the project root with:
```
GEMINI_API_KEY=YOUR_GEMINI_KEY
GEMINI_MODEL=gemini-1.5-flash   # or gemini-1.5-flash-8b
```

**Security Note**: Never commit `.env`. Keep `GEMINI_API_KEY` private.

## API Endpoints

### `GET /api/greet`
Returns a random English welcome message (text-only, no TTS).

**Response**:
```json
{
  "bot_name": "Voygan",
  "language": "en",
  "text": "Warm welcome to Voygan! I’m here to help you explore. What is your plan?",
  "audio_b64": null,
  "audio_mime": null
}
```

### `GET /api/supported-languages`
Returns a JSON object of supported languages (computed at runtime based on Gemini and gTTS compatibility).

**Response**:
```json
{ "en": "English", "fr": "French", ... }
```

### `POST /api/chat`
Ask about a place or monument; get a 5-paragraph response with optional base64-encoded MP3 audio.

**Request**:
```json
{
  "message": "Parlez-moi de la tour Eiffel.",
  "place": null,
  "tts": true
}
```

**Response**:
```json
{
  "bot_name": "Voygan",
  "language": "fr",
  "text": "...\n\n...\n\n...\n\n...\n\n...",
  "audio_b64": "BASE64_MP3...",
  "audio_mime": "audio/mpeg",
  "detected_place": null,
  "tts_ms": 430
}
```

## Screenshots
Below are screenshots of the Voygan chatbot UI in action:

| Chat UI 1 | Chat UI 2 | Chat UI 3 | Chat UI 4 |
|-----------|-----------|-----------|-----------|
| <img src="https://github.com/user-attachments/assets/84567dc4-58ce-475e-9009-93587982dce2" alt="Voygan chatbot UI 1" width="200"> | <img src="https://github.com/user-attachments/assets/a21d962b-7add-48f1-a833-874b04ea1f8b" alt="Voygan chatbot UI 2" width="200"> | <img src="https://github.com/user-attachments/assets/24bbc479-1b94-4ba1-a577-f74ab4fefe4d" alt="Voygan chatbot UI 3" width="200"> | <img src="https://github.com/user-attachments/assets/f4a8e117-125a-4667-a4b5-47af304e1540" alt="Voygan chatbot UI 4" width="200"> |

## Notes
- The backend auto-detects the user’s language from the input message.
- If the detected language isn’t supported by gTTS or Gemini, English is used as the fallback.
- The test UI is optional and can be removed by deleting the `frontend/` folder for API-only deployments.

## Curl Test Commands
Test the API with:
```bash
curl -s http://127.0.0.1:8000/api/greet | jq
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me about the Colosseum","tts":true}' | jq
```

## Configuration Tips
- **Faster replies**: Use `GEMINI_MODEL=gemini-1.5-flash-8b` (if available).
- **API-only mode**: Delete the `frontend/` folder to disable the test UI.
- **CORS**: Configure `allow_origins` in `main.py` to your app’s domain(s) before production.
- **Security**: Never expose `.env`. Consider rate limiting at your edge/proxy.

## Troubleshooting
- **“GEMINI_API_KEY missing”**: Ensure `.env` is in the project root and readable.
- **No audio**: Verify `gTTS` is installed and the machine has internet access.
- **Weird formatting**: Check `genai.py` to ensure the 5-paragraph structure is intact.
