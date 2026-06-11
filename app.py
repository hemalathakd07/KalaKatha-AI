"""
KalaKatha AI - Flask Application

Main entry point for the cultural storytelling platform.
Handles routes for home, story generation, archive, narration, and media.
"""

import json
import time
import os
import uuid
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, url_for

from config import Config
from services import (
    generate_story,
    get_story_scenes,
    generate_scene_images,
    is_valid_local_image,
    resolve_local_image_path,
)
from services.speech_to_text import save_transcript, transcribe_audio
from services.text_to_speech import generate_audio
from services.video_generator import generate_video
from services.status_tracker import update_status, get_status

# Import logging for production visibility
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KalaKatha")

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
        app.config["GENERATED_IMAGES_DIR"],
    ]:
        os.makedirs(directory, exist_ok=True)
    print("[app] Local directories verified.")


def ensure_story_images(story):
    """
    Ensure a story has valid local scene images.
    Regenerates missing or corrupt images before video creation.
    """
    story_id = story["id"]
    scene_prompts = story.get("scene_prompts") or story.get("scenes") or []
    image_urls = list(story.get("images") or [])

    if not scene_prompts:
        scene_prompts = get_story_scenes(story.get("content", ""), story.get("theme", "Folk Tale"))

    needs_regeneration = []
    for index, prompt in enumerate(scene_prompts):
        existing = image_urls[index] if index < len(image_urls) else None
        if not existing or not is_valid_local_image(existing):
            needs_regeneration.append((index, prompt))

    if needs_regeneration:
        print(f"[app] Regenerating {len(needs_regeneration)} scene image(s) for {story_id}")
        for index, prompt in needs_regeneration:
            from services.image_generator import generate_image

            url = generate_image(prompt, story_id=story_id, index=index, allow_fallback=True)
            if url:
                while len(image_urls) <= index:
                    image_urls.append(None)
                image_urls[index] = url

    image_urls = [url for url in image_urls if url and is_valid_local_image(url)]

    if image_urls != story.get("images"):
        update_story(
            story_id,
            {
                "images": image_urls,
                "scene_prompts": scene_prompts,
                "scenes": scene_prompts,
            },
        )

    return image_urls, scene_prompts


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


def run_generation_pipeline(app_instance, story_id, prompt, language, theme):
    """Background task to handle the full story-to-video pipeline."""
    with app_instance.app_context():
        try:
            # Step 1: Generate Story Text
            update_status(story_id, "generating_story")
            story_content = generate_story(prompt, language, theme)
            
            # Step 2: Extract scenes and images
            update_status(story_id, "generating_images")
            scene_prompts = get_story_scenes(story_content, theme)
            image_urls = generate_scene_images(story_id, scene_prompts)

            # Step 3: Generate Narration Audio
            update_status(story_id, "generating_audio")
            
            # Limit narration to ~2 minutes (approx 350-400 words)
            audio_text_limit = 400
            words = story_content.split()
            if len(words) > audio_text_limit:
                audio_text = " ".join(words[:audio_text_limit])
                # Attempt to end at a proper sentence boundary
                last_period = max(audio_text.rfind('.'), audio_text.rfind('।'), audio_text.rfind('!'))
                if last_period > 100: audio_text = audio_text[:last_period+1]
            else:
                audio_text = story_content

            audio_paths = generate_audio(
                audio_text,
                language=language,
                story_id=story_id,
                output_dir=app_instance.config["GENERATED_AUDIO_DIR"],
            )
            
            valid_audio_paths = [p for p in audio_paths if os.path.exists(p) and os.path.getsize(p) > 0]
            if not valid_audio_paths: raise Exception("Audio generation failed.")

            # Step 4: Generate Video
            update_status(story_id, "generating_video")
            video_url = None
            if image_urls and valid_audio_paths:
                generated_video_path = generate_video(
                    image_urls=image_urls,
                    audio_paths=valid_audio_paths,
                    story_id=story_id,
                    output_dir=app_instance.config["GENERATED_VIDEOS_DIR"]
                )
                if generated_video_path:
                    video_url = f"/static/videos/generated/{story_id}.mp4"

            # Step 5: Save Record and Finish
            audio_urls = [f"/static/audio/generated/{os.path.basename(p)}" for p in valid_audio_paths]
            story_data = {
                "id": story_id,
                "title": prompt,
                "content": story_content,
                "language": language,
                "theme": theme,
                "created_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
                "images": image_urls,
                "scene_prompts": scene_prompts,
                "scenes": scene_prompts,
                "audio": audio_urls,
                "video": video_url,
            }
            save_story(story_data)
            update_status(story_id, "completed")
            print(f"[INFO] Pipeline completed for story: {story_id}")

        except Exception as e:
            logger.error(f"Pipeline failed for {story_id}: {str(e)}")
            update_status(story_id, "failed", error=str(e))


@app.route("/status/<story_id>")
def story_status(story_id):
    """Poll the status of a background generation task."""
    status_info = get_status(story_id)
    if status_info.get("status") == "completed":
        stories = load_stories()
        story = next((s for s in stories if s["id"] == story_id), None)
        if story: status_info["story"] = story
    return jsonify(status_info)


@app.route("/generate", methods=["POST"])
def generate():
    """Generate a story from user prompt and display the result."""
    try:
        prompt = request.form.get("story_title", "").strip()
        language = request.form.get("language", "English").strip()
        theme = request.form.get("theme", "Folk Tale").strip()

        if not prompt:
            return jsonify({"success": False, "error": "Story title is required."}), 400

        if language not in SUPPORTED_LANGUAGES:
            language = "English"

        if theme not in SUPPORTED_THEMES:
            theme = "Folk Tale"

        print(f"[INFO] Selected Language: {language}")

        story_id = str(uuid.uuid4())
        ensure_directories()

        update_status(story_id, "initializing")

        # Start background pipeline thread
        thread = threading.Thread(
            target=run_generation_pipeline,
            args=(app, story_id, prompt, language, theme)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "success": True,
            "story_id": story_id
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    """Handle audio upload: Save -> Transcribe -> Generate Story -> Redirect."""
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided."}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "English")
    theme = request.form.get("theme", "Village Legend")

    if audio_file.filename == "":
        return jsonify({"success": False, "error": "No selected file."}), 400

    try:
        story_id = str(uuid.uuid4())
        ensure_directories()

        print(f"[INFO] Selected Language: {language}")

        # 1. Save the recorded audio file
        ext = os.path.splitext(audio_file.filename)[1] or ".webm"
        filename = f"{story_id}{ext}"
        audio_path = os.path.join(app.config["UPLOAD_AUDIO_DIR"], filename)
        audio_file.save(audio_path)

        # 2. Transcribe Audio to Text
        print(f"[upload-audio] Transcribing {filename}...")
        transcript = transcribe_audio(audio_path, language=language)
        
        if not transcript or len(transcript.strip()) < 5:
            return jsonify({"success": False, "error": "Recording too short or silent."}), 400

        # 3. Generate a polished story from the transcript using Gemini
        # Note: We use the existing generate_story and get_story_scenes logic
        story_content = generate_story(transcript, language, theme)
        scene_prompts = get_story_scenes(story_content, theme)

        # 4. Generate Illustrations (saved locally)
        image_urls = generate_scene_images(story_id, scene_prompts)

        # 5. Archive the Story
        story_data = {
            "id": story_id,
            "title": f"Story by Elder ({datetime.now().strftime('%Y-%m-%d')})",
            "content": story_content,
            "transcript": transcript,
            "original_audio": url_for('static', filename=f'audio/uploads/{filename}'),
            "language": language,
            "theme": theme,
            "source": "elder",
            "created_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
            "images": image_urls,
            "scene_prompts": scene_prompts,
            "scenes": scene_prompts,
            "audio": None,
            "video": None,
        }

        save_story(story_data)

        # Return both the transcript (per requirement) and the redirect (per JS needs)
        return jsonify({
            "success": True,
            "transcript": transcript,
            "redirect_url": url_for('view_story', story_id=story_id)
        })

    except Exception as e:
        logger.error(f"Voice processing failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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

    try:
        image_urls, _ = ensure_story_images(story)
    except Exception as error:
        print(f"Image preparation failed: {error}")
        return jsonify({"error": f"Could not prepare illustrations: {error}"}), 500

    if not image_urls:
        print("Error: Story has no valid local illustrations.")
        return jsonify({"error": "Story has no valid local illustrations for video generation."}), 400

    print(f"Starting Video Generation with {len(image_urls)} local images...")
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
