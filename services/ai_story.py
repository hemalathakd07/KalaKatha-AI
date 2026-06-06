import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Gemini Model
model = genai.GenerativeModel("gemini-1.5-flash")


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
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"[generate_story] Gemini API Error: {e}")
        raise e



def get_story_scenes(story_text, theme="Folk Tale"):
    """
    Analyze the story and generate scene prompts
    for image generation.
    """

    analysis_prompt = f"""
    Analyze the following {theme} story.

    Create exactly 4 visual scene descriptions.

    Each scene should be:
    - Anime style
    - Cinematic
    - Highly detailed
    - Suitable for AI image generation
    - Based on Indian culture

    Story:

    {story_text}

    Return ONLY in this format:

    SCENE 1: description

    SCENE 2: description

    SCENE 3: description

    SCENE 4: description
    """

    try:
        response = model.generate_content(analysis_prompt)

        scenes = []

        for line in response.text.split("\n"):
            if line.strip().startswith("SCENE"):
                parts = line.split(":", 1)

                if len(parts) > 1:
                    scenes.append(parts[1].strip())

        if len(scenes) >= 4:
            return scenes[:4]

    except Exception as e:
        print(f"[get_story_scenes] Error: {e}")

    return [
        "Indian village at sunrise, anime style, cinematic lighting",
        "Traditional Indian family gathering, anime style",
        "Ancient temple festival, vibrant colors, anime style",
        "Heroic cultural ending scene, cinematic anime artwork"
    ]