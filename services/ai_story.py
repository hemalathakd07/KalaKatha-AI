import os
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Gemini Model
model = genai.GenerativeModel("gemini-2.5-flash")

def generate_story(prompt, language="English", theme="Folk Tale"):
    """
    Generate a cultural story using Gemini.
    """

    full_prompt = f"""
    You are an expert Indian folklore storyteller.

    Generate a beautiful {theme} cultural story about:

    {prompt}

    Generate the entire story in {language}.

    Requirements:
    - 500 to 700 words
    - Rich Indian cultural values
    - Use proper punctuation and grammar for {language}
    - Traditional setting
    - Emotional storytelling
    - Meaningful moral lesson
    - Proper paragraphs
    - Suitable for all ages
    - Do NOT mention AI

    Return only the story.
    """

    try:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from your environment variables.")
            
        response = model.generate_content(full_prompt)
        return response.text
    except exceptions.InvalidArgument:
        print("[generate_story] Error: Invalid API Key.")
        raise Exception("Invalid Gemini API Key. Please check your .env file.")
    except exceptions.ResourceExhausted:
        print("[generate_story] Error: Quota exceeded (Rate limit).")
        raise Exception("Gemini API quota exceeded. Please try again in a few minutes.")
    except exceptions.ServiceUnavailable:
        print("[generate_story] Error: Gemini service is currently unavailable.")
        raise Exception("Gemini service is currently unavailable. Please check your network or try later.")
    except Exception as e:
        print(f"[generate_story] Gemini API Error: {e}")
        raise Exception(f"An unexpected error occurred: {str(e)}")

def get_story_scenes(story_text, theme="Folk Tale"):
    """
    Analyze the story and generate scene prompts
    for image generation.
    """

    analysis_prompt = f"""
    Analyze the following Indian {theme} story.

    Create between 4 and 6 visual scene descriptions that capture the emotional beats of the tale.

    Each scene should be:
    - Anime style
    - Cinematic
    - Highly detailed
    - Suitable for AI image generation
    - Based on Indian culture
    - Descriptions must be in English for the image generator.

    Story:

    {story_text}

    Return ONLY in this format:

    SCENE 1: description

    SCENE 2: description

    SCENE 3: description

    SCENE 4: description
    """

    try:
        if not api_key:
            raise Exception("Missing API Key")

        response = model.generate_content(analysis_prompt)

        scenes = []

        # Extract scenes using a robust split
        lines = response.text.split("\n")
        for line in lines:
            if "SCENE" in line.upper() and ":" in line:
                parts = line.split(":", 1)

                if len(parts) > 1:
                    scenes.append(parts[1].strip())

        if len(scenes) >= 4:
            return scenes

    except Exception as e:
        # Logging specific issues but returning fallback to keep the app running
        if isinstance(e, exceptions.ResourceExhausted):
            print("[get_story_scenes] Error: Quota exceeded.")
        elif isinstance(e, exceptions.InvalidArgument):
            print("[get_story_scenes] Error: Invalid API Key.")
        else:
            print(f"[get_story_scenes] Error: {e}")

    return _get_fallback_scenes()

def _get_fallback_scenes():
    return [
        "Indian village at sunrise, anime style, cinematic lighting",
        "Traditional Indian family gathering, anime style",
        "Ancient temple festival, vibrant colors, anime style",
        "Heroic cultural ending scene, cinematic anime artwork"
    ]

def _get_fallback_story(theme, language):
    """Provides a basic story if the AI fails."""
    return f"""
    This is a traditional {theme} preserved in the {language} tradition. 
    The story speaks of the eternal values of courage, community, and the 
    wisdom passed down through generations across the Indian subcontinent.
    """