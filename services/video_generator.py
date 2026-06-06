"""
Video Generation Service

Creates a simple slideshow MP4 from a story illustration and narration audio.
"""

import os
import tempfile
import urllib.request

from config import Config


def _get_moviepy():
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_audioclips
    except ImportError as error:
        raise RuntimeError(
            "moviepy is required for video generation. Install it with: pip install moviepy"
        ) from error

    return AudioFileClip, ImageClip, concatenate_audioclips


def _download_image(image_url, destination):
    request = urllib.request.Request(
        image_url,
        headers={"User-Agent": "KalaKatha-AI/1.0"},
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        image_data = response.read()

    if not image_data:
        raise ValueError("Downloaded image was empty.")

    with open(destination, "wb") as image_file:
        image_file.write(image_data)


def _create_fallback_image(destination):
    """Create a simple JPG placeholder when remote image download fails."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (1024, 1024), color=(245, 239, 230))
    draw = ImageDraw.Draw(image)
    draw.rectangle((64, 64, 960, 960), outline=(196, 168, 130), width=4)
    draw.text((512, 470), "KalaKatha AI", fill=(107, 68, 68), anchor="mm")
    draw.text((512, 540), "Illustration unavailable", fill=(138, 106, 106), anchor="mm")
    image.save(destination, format="JPEG")
    if os.path.isabs(audio_path) and os.path.exists(audio_path):
        return audio_path

    basename = os.path.basename(audio_path)
    candidate = os.path.join(base_dir, basename)
    if os.path.exists(candidate):
        return candidate

    raise FileNotFoundError(f"Audio file not found: {audio_path}")


def generate_video(image_url, audio_paths, story_id, output_dir, audio_base_dir):
    """
    Build a slideshow MP4 using one illustration and one or more MP3 files.

    Args:
        image_url (str): Pollinations or static image URL.
        audio_paths (list[str]): Absolute or static-relative MP3 paths.
        story_id (str): Story identifier for output naming.
        output_dir (str): Directory for generated MP4 files.
        audio_base_dir (str): Directory containing generated MP3 files.

    Returns:
        str: Absolute path to the generated MP4 file.
    """
    if not story_id or not output_dir:
        return None

    if not audio_paths:
        raise ValueError("At least one audio file is required.")

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{story_id}.mp4")

    if os.path.exists(output_path):
        return output_path

    resolved_audio_paths = [
        _resolve_local_audio_path(path, audio_base_dir) for path in audio_paths
    ]

    AudioFileClip, ImageClip, concatenate_audioclips = _get_moviepy()

    with tempfile.TemporaryDirectory() as temp_dir:
        image_path = os.path.join(temp_dir, "story.jpg")

        try:
            _download_image(image_url, image_path)
        except Exception:
            _create_fallback_image(image_path)

        if len(resolved_audio_paths) == 1:
            audio_clip = AudioFileClip(resolved_audio_paths[0])
        else:
            clips = [AudioFileClip(path) for path in resolved_audio_paths]
            audio_clip = concatenate_audioclips(clips)

        video_clip = (
            ImageClip(image_path)
            .with_duration(audio_clip.duration)
            .with_audio(audio_clip)
            .resized(width=1024)
        )

        video_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None,
        )

        video_clip.close()
        audio_clip.close()

    return output_path
