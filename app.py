"""
KalaKatha AI - Flask Application

Main entry point for the cultural storytelling platform.
Handles routes for home, story generation, archive, narration, and media.
"""

import json
import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, url_for

from config import Config
from services.ai_story import generate_story, get_story_scenes

from services.image_generator import generate_image
from services.speech_to_text import save_transcript
from services.text_to_speech import generate_audio
from services.video_generator import generate_video

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
        app.config["GENERATED_VIDEOS_DIR"],
        os.path.join("static", "images", "generated"),
    ]:
        os.makedirs(directory, exist_ok=True)
    print("[app] Local directories verified.")


def load_stories():
    """Load all saved stories from the JSON database."""
    db_path = app.config["DATABASE_PATH"]

    if not os.path.exists(db_path):
        return []

    with open(db_path, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def save_story(story_data):
    """Append a new story to the JSON database."""
    stories = load_stories()
    stories.insert(0, story_data)

    with open(app.config["DATABASE_PATH"], "w", encoding="utf-8") as file:
        json.dump(stories, file, indent=2, ensure_ascii=False)


def update_story(story_id, updates):
    """Update fields on an existing story in the JSON database."""
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


def cached_audio_is_valid(audio, audio_dir):
    """Verify cached audio URLs still point to existing MP3 files."""
    urls = normalize_audio_urls(audio)
    if not urls:
        return False

    for item in urls:
        basename = os.path.basename(item.split("?")[0])
        if not os.path.exists(os.path.join(audio_dir, basename)):
            return False

    return True


def get_story_audio_paths(story):
    """Return absolute MP3 paths for a story's cached narration."""
    audio = story.get("audio")
    if not audio:
        return []

    items = [audio] if isinstance(audio, str) else audio
    paths = []

    for item in items:
        basename = os.path.basename(item.split("?")[0])
        filepath = os.path.join(app.config["GENERATED_AUDIO_DIR"], basename)
        if os.path.exists(filepath):
            paths.append(filepath)

    return paths


@app.route("/")
def home():
    """Render the home page with story input form."""
    return render_template("index.html", themes=SUPPORTED_THEMES)


@app.route("/generate", methods=["POST"])
def generate():
    """Generate a story from user prompt and display the result."""
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

    try:
        story_content = generate_story(prompt, language, theme)
        scene_prompts = get_story_scenes(story_content, theme)
    except Exception as error:
        print(f"[generate] Story generation/analysis failed: {error}")
        return render_template(
            "index.html",
            themes=SUPPORTED_THEMES,
            error_message=f"Story generation failed: {str(error)}",
        ), 500

    image_urls = []
    for i, sp in enumerate(scene_prompts):
        try:
            img_url = generate_image(sp, story_id=story_id, index=i)
            if img_url:
                image_urls.append(img_url)
        except Exception as img_err:
            print(f"[generate] Image generation failed for scene {i+1}: {img_err}")

    story_data = {
        "id": story_id,
        "title": prompt,
        "content": story_content,
        "language": language,
        "theme": theme,
        "created_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "images": image_urls,
        "scene_prompts": scene_prompts,
        "audio": None,
        "video": None,
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

    ensure_directories()

    if story.get("audio") and cached_audio_is_valid(
        story["audio"], app.config["GENERATED_AUDIO_DIR"]
    ):
        return jsonify({"audio_urls": normalize_audio_urls(story["audio"])})

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


@app.route("/story/<story_id>/video")
def story_video(story_id):
    """Generate or return a slideshow video for a story."""
    print(f"\n--- VIDEO ROUTE HIT: {story_id} ---")
    stories = load_stories()
    story = next((s for s in stories if s["id"] == story_id), None)

    if not story:
        print("Error: Story not found in database")
        return jsonify({"error": "Story not found."}), 404

    ensure_directories()

    video_filename = f"{story_id}.mp4"
    video_path = os.path.join(app.config["GENERATED_VIDEOS_DIR"], video_filename)
    video_url = url_for("static", filename=f"videos/generated/{video_filename}")

    if os.path.exists(video_path):
        print(f"Returning cached video: {video_path}")
        update_story(story_id, {"video": video_url})
        return jsonify({"video_url": video_url})

    audio_paths = get_story_audio_paths(story)
    print(f"Checking existing audio paths: {audio_paths}")
    
    if not audio_paths:
        print("Audio missing. Attempting auto-generation...")
        try:
            language = story.get("language", "English")
            audio_paths = generate_audio(
                story["content"],
                language=language,
                story_id=story_id,
                output_dir=app.config["GENERATED_AUDIO_DIR"],
            )
            if audio_paths:
                audio_urls = [
                    url_for("static", filename=f"audio/generated/{os.path.basename(path)}")
                    for path in audio_paths
                ]
                update_story(story_id, {"audio": audio_urls})
            
        except Exception as e:
            print(f"Failed to auto-generate narration: {e}")
            return jsonify({"error": "Narration could not be generated for this video."}), 400

    if not audio_paths:
        print("Error: Video cannot be generated without audio.")
        return jsonify({"error": "Could not prepare narration for video."}), 500

    image_urls = story.get("images", [])
    if not image_urls:
        print("Error: Story has no image URLs.")
        return jsonify({"error": "Story has no illustrations for video generation."}), 400

    print(f"Starting Video Generation with {len(image_urls)} images...")
    try:
        generated_path = generate_video(
            image_urls=image_urls,
            audio_paths=audio_paths,
            story_id=story_id,
            output_dir=app.config["GENERATED_VIDEOS_DIR"],
            audio_base_dir=app.config["GENERATED_AUDIO_DIR"],
        )
        
        if not generated_path or not os.path.exists(generated_path):
            raise Exception("Generator returned success but file is missing.")

    except Exception as error:
        print(f"VIDEO GENERATION FAILED: {error}")
        return jsonify({"error": f"Video generation failed: {str(error)}"}), 500

    update_story(story_id, {"video": video_url})
    print(f"Success! Video URL: {video_url}")
    return jsonify({"video_url": video_url})


@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    """Store a browser-generated transcript for reuse as a story prompt."""
    data = request.get_json(silent=True) or {}
    transcript = data.get("transcript", "").strip()
    language = data.get("language", "English").strip()

    if language not in SUPPORTED_LANGUAGES:
        language = "English"

    if not transcript:
        return jsonify({"error": "Transcript cannot be empty."}), 400

    try:
        record = save_transcript(transcript, language=language)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "transcript": record["transcript"],
        "language": record["language"],
        "created_at": record["created_at"],
    })


if __name__ == "__main__":
    ensure_directories()
    app.run(debug=True)
