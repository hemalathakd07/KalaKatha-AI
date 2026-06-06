# KalaKatha AI — API Notes

This document explains the external services used by KalaKatha AI.

---

## Gemini API

**Used in:** `services/ai_story.py`

**Purpose:** Generate culturally rich story text from a user prompt.

**Model:** `gemini-2.5-flash`

**Authentication:**

Set your API key in `.env`:

```
GEMINI_API_KEY=your_key_here
```

**How it is used:**

Flask sends a structured prompt that includes:

- Story title or topic
- Selected language
- Selected cultural theme

Example instruction sent to Gemini:

```
Generate a Historical cultural story about Kolkata Tram Heritage
entirely in Bengali.
```

**Output:**

Plain-text story content (500–700 words) returned to Flask and saved in `database/stories.json`.

**Notes:**

- Requires internet access.
- Story quality depends on prompt clarity and selected theme.
- Do not expose the API key in frontend code.

---

## Pollinations AI

**Used in:** `services/image_generator.py`

**Purpose:** Generate anime-style Indian folklore illustrations from the story prompt.

**Endpoint pattern:**

```
https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024
```

**How it is used:**

1. Flask builds a prompt such as:
   `anime style Indian folklore illustration {story title}`
2. The prompt is URL-encoded.
3. A direct image URL is returned and stored in the story record.
4. The browser loads the image directly when viewing the story.

**Why `model=flux`:**

Pollinations requests without a model may return HTTP 402 (Payment Required). Using `model=flux` keeps generation on the free tier.

**Notes:**

- No API key required.
- Image generation happens when Pollinations serves the URL, so first load may take a few seconds.
- If generation fails, the story page shows a retry button.

---

## gTTS (Google Text-to-Speech)

**Used in:** `services/text_to_speech.py`

**Purpose:** Convert generated story text into spoken MP3 narration.

**Package:**

```
pip install gTTS
```

**Language mapping:**

| Story Language | gTTS Code |
|----------------|-----------|
| English        | `en`      |
| Hindi          | `hi`      |
| Kannada        | `kn`      |
| Tamil          | `ta`      |
| Bengali        | `bn`      |

**How it is used:**

1. User clicks **Listen to Story** on the story page.
2. Flask route `/story/<id>/narrate` checks if audio is already cached.
3. If not cached, gTTS generates one or more MP3 files in:
   `static/audio/generated/`
4. Audio URLs are saved back to `stories.json`.
5. The browser plays the MP3 through the narration button and HTML audio player.

**Fallback:**

If gTTS fails, the frontend falls back to browser SpeechSynthesis with the correct locale (for example `kn-IN`, `hi-IN`).

**Notes:**

- Requires internet access during first narration generation.
- Long stories are split into chunks to stay within gTTS limits.
- Cached audio avoids repeated generation on later listens.

---

## Local JSON Archive

**File:** `database/stories.json`

**Purpose:** Persist generated stories without a separate database server.

**Example story object:**

```json
{
  "id": "uuid",
  "title": "Kolkata Tram Heritage",
  "content": "...",
  "language": "Bengali",
  "theme": "Historical",
  "created_at": "June 05, 2026 at 10:54 PM",
  "images": [
    "https://image.pollinations.ai/prompt/..."
  ],
  "audio": [
    "/static/audio/generated/uuid.mp3"
  ]
}
```

---

## Environment Summary

| Service        | Key Required | Used For              |
|----------------|--------------|-----------------------|
| Gemini API     | Yes          | Story text generation |
| Pollinations AI| No           | Illustration URLs     |
| gTTS           | No           | Narration MP3 files   |
| JSON file      | No           | Story archive storage |
