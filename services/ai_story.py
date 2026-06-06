import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_story(prompt, language="English", theme="Folk Tale"):
    full_prompt = f"""
    You are an expert Indian folklore storyteller.

    Generate a {theme} cultural story about {prompt}
    entirely in {language}.

    Include:
    - Indian cultural values
    - Traditional setting
    - Emotional storytelling
    - 500-700 words
    - Proper paragraphs

    Do not mention AI.
    """

    response = model.generate_content(full_prompt)

    return response.text
