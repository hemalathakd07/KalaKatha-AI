import os
import re

import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print("[INFO] Gemini API key loaded:", bool(api_key))
def list_available_models():
    """
    List available Gemini models for the current API key.
    Useful for diagnostics and selecting available endpoints.
    """
    if not api_key:
        print("[ERROR] API Key not found. Cannot list models.")
        return []
    try:
        genai.configure(api_key=api_key)
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        return available_models
    except Exception as e:
        print(f"[ERROR] Failed to list Gemini models: {e}")
        return []

def initialize_gemini_model():
    """
    Initializes the Gemini model with fallback logic to ensure the app doesn't crash 
    if a specific model version is unavailable.
    """
    if not api_key:
        return None

    genai.configure(api_key=api_key)
    
    # Priority list for selection. 
    # gemini-2.5-flash and gemini-2.0-flash are added as requested fallbacks.
    preferred_models = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-pro"
    ]
    
    available_models = list_available_models()
    
    if not available_models:
        print("[WARNING] No models found via list_models(). Trying default 'gemini-1.5-flash'.")
        return genai.GenerativeModel("gemini-1.5-flash")

    for model_id in preferred_models:
        # Check if requested model id is in the list
        match = next((m for m in available_models if model_id in m), None)
        if match:
            print(f"[INFO] Gemini Model initialized: {match}")
            return genai.GenerativeModel(match)
            
    # If no preferred model matches, pick the first one from the available list
    print(f"[INFO] Using first available model: {available_models[0]}")
    return genai.GenerativeModel(available_models[0])

# Initialize the model globally
model = initialize_gemini_model()

CULTURAL_STORY_TEMPLATES = {
    "Mythology": (
        "Long ago in the sacred land of Bharata, where rivers whispered ancient hymns and "
        "temple bells rang at dawn, a noble hero walked the path of dharma. Though trials "
        "arose and shadows tested their courage, devotion, truth, and compassion guided every "
        "step. Elders gathered beneath the banyan tree to say that righteousness outlives every "
        "storm, and that a heart rooted in duty becomes a light for future generations."
    ),
    "Folk Tale": (
        "In a quiet Indian village surrounded by fields and festival lamps, an ordinary person "
        "faced an unexpected challenge. With wit, kindness, and help from neighbors, they "
        "turned hardship into wisdom. The tale reminds us that humility, friendship, and "
        "clever thinking can protect even the smallest among us."
    ),
    "Historical": (
        "Across the courtyards and market streets of old India, a moment of history unfolded "
        "that would be remembered for generations. Artists, scholars, traders, and farmers "
        "each carried forward the living memory of their culture. The story honors those who "
        "preserved tradition while embracing change."
    ),
    "Festival": (
        "As drums echoed and lamps glowed across the village, families prepared for a beloved "
        "festival that united young and old. Songs, sweets, rituals, and laughter filled the "
        "night air, teaching children that celebration is also remembrance. The gathering "
        "became a promise to keep cultural joy alive."
    ),
    "Village Legend": (
        "Grandmother's voice softened as she recalled a legend known only in their village. "
        "Near the old well and the neem tree, something extraordinary once happened to someone "
        "brave and kind. The legend survived because each listener chose to tell it again, "
        "passing courage and community from one generation to the next."
    ),
}


def generate_story(prompt, language="English", theme="Folk Tale"):
    """Generate a cultural story using Gemini, with template fallback on quota errors."""
    print(f"[INFO] Story Language: {language}")
    full_prompt = f"""
    You are an expert Indian folklore storyteller.

    Generate a beautiful {theme} cultural story about:

    {prompt}

    Generate this entire story in {language} language.

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
        if not api_key or model is None:
            raise ValueError("GEMINI_API_KEY is missing from your environment variables.")

        response = model.generate_content(full_prompt)
        if response and response.text:
            print("[INFO] Gemini Response Received")
            return response.text.strip()
        else:
            print("[ERROR] Gemini returned an empty response.")
            return _get_fallback_story(theme, language, prompt)
    except exceptions.InvalidArgument:
        print("[generate_story] Error: Invalid API Key.")
        raise Exception("Invalid Gemini API Key. Please check your .env file.")
    except exceptions.ResourceExhausted as e:
        print(f"[ERROR] Quota exceeded: {e}. Using cultural template fallback.")
        return _get_fallback_story(theme, language, prompt)
    except exceptions.ServiceUnavailable as e:
        print(f"[ERROR] Gemini service unavailable: {e}. Using template fallback.")
        return _get_fallback_story(theme, language, prompt)
    except Exception as error:
        print(f"[ERROR] Gemini API Error: {error}")
        if "quota" in str(error).lower() or "429" in str(error):
            return _get_fallback_story(theme, language, prompt)
        raise Exception(f"An unexpected error occurred: {str(error)}")


def get_story_scenes(story_text, theme="Folk Tale"):
    """
    Extract exactly 5 unique visual scene prompts from story content locally.
    This avoids additional Gemini API calls and potential quota issues.
    """
    scenes = extract_scenes_from_story(story_text, theme=theme)

    print("[INFO] Story analyzed successfully")
    for i, s in enumerate(scenes):
        print(f"[INFO] Scene {i+1}: {s}")

    return scenes


def extract_scenes_from_story(story_text, theme="Folk Tale", target_count=5):
    """Derive unique scene prompts locally from story text by selecting key narrative segments."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", story_text or "") if p.strip()]
    
    # If few paragraphs, split by sentences for better diversity
    if len(paragraphs) < target_count:
        all_text = " ".join(paragraphs)
        segments = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", all_text) if s.strip()]
    else:
        segments = paragraphs

    # Ensure we have at least 5 segments (pad if necessary)
    while len(segments) < target_count:
        segments.append(f"A peaceful moment in a {theme} setting.")

    # Pick 5 segments across the story duration to represent key events
    n = len(segments)
    indices = [0, n // 4, n // 2, (3 * n) // 4, n - 1]
    
    # Handle potential duplicates for small n
    unique_indices = []
    seen = set()
    for idx in indices:
        while idx in seen and idx < n - 1:
            idx += 1
        unique_indices.append(idx)
        seen.add(idx)

    labels = ["Introduction", "Conflict", "Journey", "Climax", "Resolution"]
    scenes = []

    for i, seg_idx in enumerate(unique_indices):
        label = labels[i]
        text_block = segments[seg_idx]
        
        # Clean and extract a visual prompt
        sentence = re.split(r"(?<=[.!?।])\s+", text_block)[0].strip()
        excerpt = sentence if len(sentence) >= 40 else text_block[:150].strip()
        excerpt = re.sub(r'[*#_]', '', excerpt)

        scenes.append(
            f"{theme} {label}: {excerpt}, Studio Ghibli style, anime cinematic composition, Indian cultural setting"
        )

    return scenes


def _get_fallback_story(theme, language, prompt):
    template = CULTURAL_STORY_TEMPLATES.get(theme, CULTURAL_STORY_TEMPLATES["Folk Tale"])
    return (
        f"In {language}, this preserved {theme.lower()} speaks of {prompt.strip()}. "
        f"{template}"
    ).strip()
