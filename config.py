import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration settings."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "kalakatha_secret_key")

    # Paths for data storage
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "stories.json")
    UPLOAD_AUDIO_DIR = os.path.join(BASE_DIR, "uploads", "audio")
    GENERATED_IMAGES_DIR = os.path.join(BASE_DIR, "static", "images", "generated")
    GENERATED_AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio", "generated")

    # Future API keys (load from .env when ready)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
