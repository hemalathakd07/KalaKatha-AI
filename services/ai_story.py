import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"

# Initialize Groq client
client = Groq(api_key=api_key) if api_key else None

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
    """Generate a cultural story using Groq with template fallback."""
    print("[INFO] Generating story using Groq")
    print(f"[INFO] Story Language: {language} | Theme: {theme}")
    
    full_prompt = f"""
    You are an expert Indian folklore storyteller.
    Generate a beautiful {theme} cultural story about:
    {prompt}

    CRITICAL: Generate the entire story in {language} language. 
    Do NOT use English unless the requested language is English.

    Requirements:
    - Length: 700 to 1200 words
    - Rich Indian cultural values
    - Use proper punctuation and grammar for {language}
    - Traditional setting
    - Emotional storytelling
    - Include a clear beginning, conflict, journey, climax, and a meaningful moral ending.
    - Proper paragraphs
    - Suitable for all ages
    - Do NOT mention AI

    Return only the story.
    """

    try:
        if not api_key or client is None:
            raise ValueError("GROQ_API_KEY is missing from your environment variables.")

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional storyteller specializing in Indian culture and folklore."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
        )

        story_text = completion.choices[0].message.content
        if story_text:
            print("[INFO] Story generated successfully")
            return story_text.strip()
        else:
            print("[ERROR] Groq returned an empty response.")
            return _get_fallback_story(theme, language, prompt)
            
    except Exception as error:
        print(f"[ERROR] Groq API Error: {error}")
        return _get_fallback_story(theme, language, prompt)


def get_story_scenes(story_text, theme="Folk Tale"):
    """
    Extract exactly 5 unique visual scene prompts from story content using Groq.
    Falls back to local extraction if the API call fails.
    """
    print("[INFO] Generating scene prompts using Groq")
    
    scene_extraction_prompt = f"""
    You are a storyboard artist and visual prompt engineer. Analyze the provided {theme} story and identify exactly 5 distinct, visually rich narrative beats representing: Introduction, Conflict, Journey, Climax, and Resolution.

    For each beat, write a single descriptive visual sentence optimized for an AI image generator. 
    Focus on characters, traditional Indian settings, lighting, and emotions.
    
    Requirements:
    - Exactly 5 scenes.
    - Each scene must be visually different.
    - Return ONLY the descriptions, one per line.
    - Do NOT include labels like 'Scene 1', numbers, or headers.
    - Avoid duplicate visual themes.

    Story:
    {story_text[:3000]}
    """

    try:
        if not client:
            raise ValueError("Groq client not initialized")
            
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a visual artist. Your task is to extract scene descriptions for illustrations."},
                {"role": "user", "content": scene_extraction_prompt}
            ],
            temperature=0.5,
        )
        
        content = completion.choices[0].message.content.strip()
        lines = [line.strip() for line in content.splitlines() if len(line.strip()) > 10]
        
        # Take only the first 5 and append the styling suffix
        raw_scenes = lines[:5]
        
        if len(raw_scenes) < 5:
            raise ValueError("Insufficient scenes returned by Groq")
            
        scenes = [
            f"{s}, Studio Ghibli style, anime cinematic composition, Indian cultural setting" 
            for s in raw_scenes
        ]
        print("[INFO] Scene prompts generated successfully")
        
    except Exception as e:
        print(f"[WARNING] Groq scene extraction failed: {e}. Falling back to local logic.")
        scenes = extract_scenes_from_story(story_text, theme=theme, target_count=5)

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
