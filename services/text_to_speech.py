"""
Text-to-Speech Service

Generates narration audio using gTTS with multilingual support.
"""

import os
import re

from gtts import gTTS

LANGUAGE_CODES = {
    "English": "en",
    "Kannada": "kn",
    "Hindi": "hi",
    "Tamil": "ta",
    "Bengali": "bn",
}

MAX_CHUNK_CHARS = 4500


def _split_text(text, max_chars=MAX_CHUNK_CHARS):
    """Split long story text into gTTS-safe chunks at paragraph boundaries."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        sentences = re.split(r"(?<=[.!?।])\s+", paragraph)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            candidate = f"{current} {sentence}".strip() if current else sentence

            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = sentence

    if current:
        chunks.append(current)

    return chunks or [text[:max_chars]]


def generate_audio(text, language="English", story_id=None, output_dir=None):
    """
    Convert story text into spoken narration audio files.

    Args:
        text (str): Story content to narrate.
        language (str): Story language name (English, Kannada, etc.).
        story_id (str): Unique story identifier for file naming.
        output_dir (str): Directory to save generated MP3 files.

    Returns:
        list[str]: Absolute paths to generated audio files.
    """
    if not text or not story_id or not output_dir:
        return []

    lang_code = LANGUAGE_CODES.get(language, "en")
    os.makedirs(output_dir, exist_ok=True)

    chunks = _split_text(text)
    audio_paths = []

    for index, chunk in enumerate(chunks):
        suffix = f"_{index}" if len(chunks) > 1 else ""
        filename = f"{story_id}{suffix}.mp3"
        filepath = os.path.join(output_dir, filename)

        if not os.path.exists(filepath):
            tts = gTTS(text=chunk, lang=lang_code)
            tts.save(filepath)

        audio_paths.append(filepath)

    return audio_paths
