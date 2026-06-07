import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration settings."""

    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "kalakatha_secret_key")

    # Paths for data storage
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "stories.json")
    UPLOAD_AUDIO_DIR = os.path.join(BASE_DIR, "uploads", "audio")
    GENERATED_IMAGES_DIR = os.path.join(BASE_DIR, "static", "images", "generated")
    GENERATED_AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio", "generated")
    GENERATED_VIDEOS_DIR = os.path.join(BASE_DIR, "static", "videos", "generated")
    TRANSCRIPTS_PATH = os.path.join(BASE_DIR, "database", "transcripts.json")

    # API keys (load from .env)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")
