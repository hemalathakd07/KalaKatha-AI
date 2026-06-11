import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("Key loaded:", api_key[:15] + "...")

genai.configure(api_key=api_key)

try:
    models = genai.list_models()

    print("\nAvailable Models:\n")

    for model in models:
        print(model.name)

except Exception as e:
    print("ERROR:", e)