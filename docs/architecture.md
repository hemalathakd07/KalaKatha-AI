# KalaKatha AI — System Architecture

KalaKatha AI is a cultural storytelling platform that turns user prompts into preserved digital folk tales with illustrations and narration.

## High-Level Flow

```
Frontend (HTML / CSS / JavaScript)
        ↓
Flask Server (app.py)
        ↓
Gemini API (services/ai_story.py)
        ↓
Scene Extraction
        ↓
Pollinations AI (services/image_generator.py)
        ↓
gTTS (services/text_to_speech.py)
        ↓
JSON Archive Database (database/stories.json)
```

## Components

### Frontend

- **templates/index.html** — Story creation form with language and theme selectors.
- **templates/story.html** — Displays generated story, Pollinations illustration, and narration controls.
- **templates/archive.html** — Lists all saved stories with theme and language badges.
- **static/js/script.js** — Form loading states, image gallery retry logic, gTTS playback, and browser SpeechSynthesis fallback.
- **static/css/style.css** — Shared styling for cards, badges, gallery, and audio player.

### Flask Server

- **app.py** — Main application entry point.
- Routes:
  - `GET /` — Home page
  - `POST /generate` — Generate and save a story
  - `GET /archive` — View saved stories
  - `GET /story/<id>` — View a single story
  - `GET /story/<id>/narrate` — Generate or return cached gTTS audio

### Gemini API

- **services/ai_story.py**
- Uses Google Gemini (`gemini-2.5-flash`) to generate culturally rich stories.
- Accepts:
  - **prompt** — Story title or topic
  - **language** — English, Kannada, Hindi, Tamil, Bengali
  - **theme** — Mythology, Folk Tale, Historical, Festival, Village Legend

### Pollinations AI

- **services/image_generator.py**
- Builds a direct image URL using Pollinations AI with the `flux` model.
- No local image download — the browser loads the remote URL directly.
- Images are stored as URLs inside each story record under `"images"`.

### gTTS

- **services/text_to_speech.py**
- Converts story text into MP3 narration using Google Text-to-Speech.
- Supports multilingual narration:
  - English → `en`
  - Hindi → `hi`
  - Kannada → `kn`
  - Tamil → `ta`
  - Bengali → `bn`
- Long stories are split into chunks and saved under `static/audio/generated/`.
- Audio is generated on first listen and cached in `stories.json`.

### JSON Archive Database

- **database/stories.json**
- Stores all generated stories locally.
- Each story includes:
  - `id`
  - `title`
  - `content`
  - `language`
  - `theme`
  - `created_at`
  - `images`
  - `audio`

## Story Generation Sequence

1. User submits title, language, and theme from the homepage.
2. Flask calls Gemini to generate the story text.
3. Flask builds a Pollinations image URL from the prompt.
4. Flask saves the story object to `stories.json`.
5. Flask renders `story.html`.
6. When the user clicks **Listen to Story**, Flask generates gTTS audio if not already cached.
7. The browser plays the MP3 and shows an HTML audio player.

## Configuration

- **config.py** — Paths, secret key, and API key loading.
- **.env** — Stores `GEMINI_API_KEY`.

## Design Goals

- Preserve Indian cultural storytelling traditions.
- Support multilingual generation and narration.
- Keep the archive simple and portable using JSON storage.
- Use free-tier friendly services where possible (Pollinations AI, gTTS).
