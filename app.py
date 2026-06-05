"""
KalaKatha AI - Flask Application

Main entry point for the cultural storytelling platform.
Handles routes for home, story generation, and archive.
"""

import json
import os
import uuid
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

from config import Config
from services.ai_story import generate_story

app = Flask(__name__)
app.config.from_object(Config)


def ensure_directories():
    """Create required directories if they do not exist."""
    for directory in [
        os.path.dirname(app.config["DATABASE_PATH"]),
        app.config["UPLOAD_AUDIO_DIR"],
        app.config["GENERATED_IMAGES_DIR"],
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


@app.route("/")
def home():
    """Render the home page with story input form."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate a story from user prompt and display the result.

    Reads the story title from the form, calls the AI story service,
    saves to database, and renders story.html.
    """
    prompt = request.form.get("story_title", "").strip()

    if not prompt:
        return redirect(url_for("home"))

    # Generate story content using AI service (dummy for now)
    story_content = generate_story(prompt)

    # Build story object for storage and display
    story_data = {
        "id": str(uuid.uuid4()),
        "title": prompt,
        "content": story_content,
        "created_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "images": [],
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


if __name__ == "__main__":
    ensure_directories()
    app.run(debug=True)
