"""
Speech-to-Text Service

Lightweight transcript storage for browser Web Speech API results.
No paid APIs — transcription happens in the browser.
"""

import json
import os
from datetime import datetime
import speech_recognition as sr
from pydub import AudioSegment

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


def transcribe_audio(audio_path, language="English"):
    """
    Convert an audio file into text using Google Speech Recognition.
    Supports dynamic language mapping.
    """
    lang_map = {
        "English": "en-US",
        "Kannada": "kn-IN",
        "Hindi": "hi-IN",
        "Tamil": "ta-IN",
        "Bengali": "bn-IN"
    }
    target_lang = lang_map.get(language, "en-US")
    
    recognizer = sr.Recognizer()
    
    # Convert to WAV if needed (SpeechRecognition works best with WAV)
    if not audio_path.endswith('.wav'):
        try:
            wav_path = audio_path.rsplit('.', 1)[0] + ".wav"
            audio = AudioSegment.from_file(audio_path)
            audio.export(wav_path, format="wav")
            audio_path = wav_path
        except Exception as e:
            print(f"[stt] Audio conversion failed: {e}")
            raise ValueError("Could not process audio format. Ensure FFmpeg is installed.")

    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=target_lang)
            return text
    except sr.UnknownValueError:
        raise ValueError("Speech was unintelligible. Please try a clearer recording.")
    except sr.RequestError as e:
        raise Exception(f"STT Service unavailable: {e}")


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
