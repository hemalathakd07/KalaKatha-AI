import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API Key Loaded:", api_key[:15] + "...")

genai.configure(api_key=api_key)

models_to_test = [
    "gemini-1.5-flash",
]

for model_name in models_to_test:
    print(f"\nTesting {model_name} ...")

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            "Reply with exactly one word: Hello"
        )

        print("SUCCESS")
        print(response.text)

    except Exception as e:
        print("FAILED")
        print(e)