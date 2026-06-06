import google.genai as genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_story(prompt, language="English", theme="Folk Tale"):
    full_prompt = f"""
    You are an expert Indian folklore storyteller.

    Generate a {theme} cultural story about {prompt}
    entirely in {language}.

    Include:
    - Indian cultural values
    - Traditional setting
    - Emotional storytelling
    - 400-600 words
    - Proper paragraphs (at least 4-5 paragraphs)

    Do not mention AI.
    """

    response = client.models.generate_content(model="gemini-2.0-flash", contents=full_prompt)
    return response.text


def get_story_scenes(story_text, theme="Folk Tale"):
    """
    Analyzes the story and returns 4-5 visual scene descriptions for image generation.
    """
    analysis_prompt = f"""
    Analyze this {theme} story and break it into 4 distinct visual scenes for an anime-style video.
    For each scene, provide a short, highly descriptive visual prompt (focus on characters, environment, and mood).
    
    Story: {story_text}

    Return the result in this exact format:
    SCENE 1: [Prompt]
    SCENE 2: [Prompt]
    SCENE 3: [Prompt]
    SCENE 4: [Prompt]
    """
    
    response = client.models.generate_content(model="gemini-2.0-flash", contents=analysis_prompt)
    scenes = []
    for line in response.text.split("\n"):
        if line.startswith("SCENE"):
            prompt = line.split(":", 1)[1].strip()
            scenes.append(prompt)
    
    return scenes if scenes else ["Traditional Indian folk scene, anime style"]
