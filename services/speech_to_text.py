"""
Speech-to-Text Service

Lightweight transcript storage for browser Web Speech API results.
No paid APIs — transcription happens in the browser.
"""

import json
import os
from datetime import datetime

from config import Config

TRANSCRIPTS_PATH = Config.TRANSCRIPTS_PATH


def _load_transcripts():
    if not os.path.exists(TRANSCRIPTS_PATH):
        return []

    with open(TRANSCRIPTS_PATH, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def save_transcript(transcript, language="English"):
    """
    Persist a browser-generated transcript for later reuse.

    Args:
        transcript (str): Speech-to-text output from the browser.
        language (str): Selected story language.

    Returns:
        dict: Saved transcript record.
    """
    cleaned = (transcript or "").strip()
    if not cleaned:
        raise ValueError("Transcript cannot be empty.")

    record = {
        "transcript": cleaned,
        "language": language,
        "created_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
    }

    transcripts = _load_transcripts()
    transcripts.insert(0, record)

    os.makedirs(os.path.dirname(TRANSCRIPTS_PATH), exist_ok=True)
    with open(TRANSCRIPTS_PATH, "w", encoding="utf-8") as file:
        json.dump(transcripts, file, indent=2, ensure_ascii=False)

    return record
