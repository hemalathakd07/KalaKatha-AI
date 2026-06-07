import os
import re

import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print("[INFO] Gemini API key loaded:", bool(api_key))
if api_key:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash") if api_key else None

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
    """Extract exactly 5 unique visual scene prompts from story content."""
    analysis_prompt = f"""
    Analyze the following Indian {theme} story.
    Create exactly 5 visual scene descriptions that capture the emotional beats of the tale.
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
    SCENE 5: description
    """

    scenes = []
    try:
        if api_key and model is not None:
            response = model.generate_content(analysis_prompt)
            extracted = _parse_scene_lines(response.text)
            if len(extracted) >= 3:
                scenes = extracted[:5]
    except exceptions.ResourceExhausted:
        print("[get_story_scenes] Error: Quota exceeded. Using local scene extraction.")
    except exceptions.InvalidArgument:
        print("[get_story_scenes] Error: Invalid API Key. Using local scene extraction.")
    except Exception as error:
        print(f"[get_story_scenes] Error: {error}. Using local scene extraction.")

    if not scenes:
        scenes = extract_scenes_from_story(story_text, theme=theme)

    # Final check to ensure exactly 5 and add labels for uniqueness
    if len(scenes) < 5:
        fallback = _get_fallback_scenes(theme)
        scenes.extend(fallback[len(scenes):5])

    print("[INFO] Scene prompts generated:")
    for i, s in enumerate(scenes):
        print(f"  {s}")

    return scenes


def extract_scenes_from_story(story_text, theme="Folk Tale", target_count=5):
    """Derive unique scene prompts locally from story text when Gemini is unavailable."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", story_text or "") if p.strip()]
    
    # If few paragraphs, split by sentences for better diversity
    if len(paragraphs) < target_count:
        all_text = " ".join(paragraphs)
        segments = [s.strip() for s in re.split(r"(?<=[.!?।])\s+", all_text) if s.strip()]
    else:
        segments = paragraphs

    if len(segments) < target_count:
        print(f"[extract_scenes_from_story] Insufficient content ({len(segments)} segments). Using template defaults.")
        return _get_fallback_scenes(theme)

    labels = ["Introduction", "Conflict", "Journey", "Climax", "Moral ending"]
    chosen = segments[:target_count]

    scenes = []
    for i, text_block in enumerate(chosen):
        label = labels[i] if i < len(labels) else f"Part {i+1}"
        # Use the first sentence or a short excerpt
        sentence = re.split(r"(?<=[.!?।])\s+", text_block)[0].strip()
        excerpt = sentence if len(sentence) >= 40 else text_block[:200].strip()
        scenes.append(
            f"{theme} {label}: {excerpt}, anime cinematic composition, Indian cultural setting"
        )
    return scenes


def _parse_scene_lines(text):
    scenes = []
    for line in (text or "").split("\n"):
        upper = line.upper()
        if "SCENE" in upper and ":" in line:
            parts = line.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                scenes.append(parts[1].strip())
    return scenes


def _get_fallback_scenes(theme="Folk Tale"):
    return [
        f"{theme} Introduction: Indian village at sunrise with elders gathering, anime cinematic lighting",
        f"{theme} Conflict: Traditional Indian family facing a challenge in a courtyard, detailed anime art",
        f"{theme} Journey: A traveler walking through vibrant Indian landscapes, anime masterpiece",
        f"{theme} Climax: Heroic resolution of the story in a dramatic setting, cinematic anime artwork",
        f"{theme} Moral ending: Peaceful scene beneath a banyan tree at golden hour, Studio Ghibli style",
    ]


def _get_fallback_story(theme, language, prompt):
    template = CULTURAL_STORY_TEMPLATES.get(theme, CULTURAL_STORY_TEMPLATES["Folk Tale"])
    return (
        f"In {language}, this preserved {theme.lower()} speaks of {prompt.strip()}. "
        f"{template}"
    ).strip()
