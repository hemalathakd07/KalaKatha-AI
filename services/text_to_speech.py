"""
Text-to-Speech Service

Generates narration audio using gTTS with multilingual support.
"""

import asyncio
import os
import re
import time
import traceback

from gtts import gTTS
import edge_tts

LANGUAGE_CODES = {
    "English": "en",
    "Kannada": "kn",
    "Hindi": "hi",
    "Tamil": "ta",
    "Bengali": "bn",
}

EDGE_VOICES = {
    "English": "en-IN-NeerjaNeural",
    "Hindi": "hi-IN-SwaraNeural",
    "Kannada": "kn-IN-SapnaNeural",
    "Tamil": "ta-IN-PallaviNeural",
    "Telugu": "te-IN-ShrutiNeural",
    "Malayalam": "ml-IN-SobhanaNeural",
    "Bengali": "bn-IN-TanishaaNeural",
    "Marathi": "mr-IN-AarohiNeural",
}

MAX_CHUNK_CHARS = 4000


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


async def _generate_edge_audio(text, voice, filepath):
    """Helper for async Edge-TTS generation."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)


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
    print("\n[TTS] Starting narration")
    print(f"[TTS] Language: {language}")
    print(f"[TTS] Story length: {len(text) if text else 0}")

    if not text or not story_id or not output_dir:
        print("[TTS] Error: Missing required parameters (text, story_id, or output_dir)")
        return []

    os.makedirs(output_dir, exist_ok=True)
    chunks = _split_text(text)
    audio_paths = []

    for index, chunk in enumerate(chunks):
        suffix = f"_{index}" if len(chunks) > 1 else ""
        filename = f"{story_id}{suffix}.mp3"
        filepath = os.path.join(output_dir, filename)
        print(f"[TTS] Output path: {filepath}")

        if not os.path.exists(filepath):
            success = False
            
            # 1. Try Edge-TTS first
            try:
                print("[TTS] Using Edge-TTS")
                voice = EDGE_VOICES.get(language, "en-IN-NeerjaNeural")
                print(f"[TTS] Selected voice: {voice}")
                
                asyncio.run(_generate_edge_audio(chunk, voice, filepath))
                
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    success = True
                    print("[TTS] Audio generated successfully via Edge-TTS")
            except Exception as e:
                print(f"[TTS] Edge-TTS failed: {str(e)}")
                traceback.print_exc()

            # 2. Try gTTS fallback if Edge-TTS failed
            if not success:
                lang_code = LANGUAGE_CODES.get(language, "en")
                print(f"[TTS] Using gTTS fallback (Code: {lang_code})")
                
                # Automatic Retry Logic
                for attempt in range(2):
                    try:
                        if attempt > 0:
                            print(f"[TTS] gTTS Retry Attempt {attempt}...")
                            time.sleep(2)
                        
                        tts = gTTS(text=chunk, lang=lang_code)
                        tts.save(filepath)
                        
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            success = True
                            print("[TTS] Audio generated successfully via gTTS")
                            break
                    except Exception as g_err:
                        print(f"[TTS] gTTS attempt {attempt} failed: {str(g_err)}")
                        if attempt == 1:
                            traceback.print_exc()

            if not success:
                error_detail = f"All TTS providers failed for {language}."
                print(f"[TTS] CRITICAL ERROR: {error_detail}")
                # Clean up empty file if created
                if os.path.exists(filepath):
                    os.remove(filepath)
                return audio_paths # Return what we have so far

        # Verification
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            size_kb = os.path.getsize(filepath) / 1024
            print(f"[TTS] Audio file size: {size_kb:.2f} KB")
            audio_paths.append(filepath)
        else:
            print(f"[TTS] Verification failed for {filepath}: File missing or 0 bytes")

    return audio_paths
