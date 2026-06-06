"""
KalaKatha AI - Flask Application

Main entry point for the cultural storytelling platform.
Handles routes for home, story generation, and archive.
"""

import json
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, url_for

from config import Config
from services.ai_story import generate_story
from services.image_generator import generate_image
from services.text_to_speech import generate_audio

SUPPORTED_LANGUAGES = ("English", "Kannada", "Hindi", "Tamil", "Bengali")
SUPPORTED_THEMES = (
    "Mythology",
    "Folk Tale",
    "Historical",
    "Festival",
    "Village Legend",
)

app = Flask(__name__)
app.config.from_object(Config)


def ensure_directories():
    """Create required directories if they do not exist."""
    for directory in [
        os.path.dirname(app.config["DATABASE_PATH"]),
        app.config["UPLOAD_AUDIO_DIR"],
        app.config["GENERATED_AUDIO_DIR"],
    ]:
        os.makedirs(directory, exist_ok=True)


def load_stories():
    """
    Load all saved stories from the JSON database.

    Returns:
        list: List of story dictionaries.
    """
    db_path = app.config["DATABASE_PATH"]

    if not os.path.exists(db_path):
        return []

    with open(db_path, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def save_story(story_data):
    """
    Append a new story to the JSON database.

    Args:
        story_data (dict): Story object to save.
    """
    stories = load_stories()
    stories.insert(0, story_data)

    with open(app.config["DATABASE_PATH"], "w", encoding="utf-8") as file:
        json.dump(stories, file, indent=2, ensure_ascii=False)


def update_story(story_id, updates):
    """
    Update fields on an existing story in the JSON database.

    Args:
        story_id (str): Story UUID.
        updates (dict): Fields to merge into the story record.
    """
    stories = load_stories()

    for index, story in enumerate(stories):
        if story["id"] == story_id:
            stories[index].update(updates)
            break

    with open(app.config["DATABASE_PATH"], "w", encoding="utf-8") as file:
        json.dump(stories, file, indent=2, ensure_ascii=False)


def normalize_audio_urls(audio):
    """Convert stored audio paths into a list of playable URLs."""
    if not audio:
        return []

    if isinstance(audio, str):
        if audio.startswith("http") or audio.startswith("/"):
            return [audio]
        return [url_for("static", filename=audio)]

    urls = []
    for item in audio:
        if item.startswith("http") or item.startswith("/"):
            urls.append(item)
        else:
            urls.append(url_for("static", filename=item))
    return urls


@app.route("/")
def home():
    """Render the home page with story input form."""
    return render_template("index.html", themes=SUPPORTED_THEMES)


@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate a story from user prompt and display the result.

    Reads the story title from the form, calls the AI story service,
    saves to database, and renders story.html.
    """
    prompt = request.form.get("story_title", "").strip()
    language = request.form.get("language", "English").strip()
    theme = request.form.get("theme", "Folk Tale").strip()

    if not prompt:
        return redirect(url_for("home"))

    if language not in SUPPORTED_LANGUAGES:
        language = "English"

    if theme not in SUPPORTED_THEMES:
        theme = "Folk Tale"

    story_id = str(uuid.uuid4())
    story_content = generate_story(prompt, language, theme)
    image_url = generate_image(prompt, story_id=story_id)

    story_data = {
        "id": story_id,
        "title": prompt,
        "content": story_content,
        "language": language,
        "theme": theme,
        "created_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "images": [image_url],
        "audio": None,
    }

    save_story(story_data)

    return render_template("story.html", story=story_data)


@app.route("/archive")
def archive():
    """Display all saved stories from the digital archive."""
    stories = load_stories()
    return render_template("archive.html", stories=stories)


@app.route("/story/<story_id>")
def view_story(story_id):
    """View a single story from the archive by its ID."""
    stories = load_stories()
    story = next((s for s in stories if s["id"] == story_id), None)

    if not story:
        return redirect(url_for("archive"))

    return render_template("story.html", story=story)


@app.route("/story/<story_id>/narrate")
def narrate_story(story_id):
    """Generate or return cached narration audio for a story."""
    stories = load_stories()
    story = next((s for s in stories if s["id"] == story_id), None)

    if not story:
        return jsonify({"error": "Story not found."}), 404

    if story.get("audio"):
        return jsonify({"audio_urls": normalize_audio_urls(story["audio"])})

    ensure_directories()

    language = story.get("language", "English")
    audio_paths = generate_audio(
        story["content"],
        language=language,
        story_id=story_id,
        output_dir=app.config["GENERATED_AUDIO_DIR"],
    )

    if not audio_paths:
        return jsonify({"error": "Could not generate narration."}), 500

    audio_urls = [
        url_for("static", filename=f"audio/generated/{os.path.basename(path)}")
        for path in audio_paths
    ]

    update_story(story_id, {"audio": audio_urls})

    return jsonify({"audio_urls": audio_urls})


if __name__ == "__main__":
    ensure_directories()
    app.run(debug=True)
