"""
Video Generation Service

Creates a cinematic slideshow from LOCAL scene images and narration audio.
"""

import os
import time

from PIL import Image

from config import Config
from .image_generator import resolve_local_image_path, validate_image

try: # MoviePy 2.0+ uses vfx for fade effects
    from moviepy import (
        ImageClip, 
        AudioFileClip, 
        concatenate_videoclips, 
        concatenate_audioclips,
        CompositeVideoClip
    )
    print("[video_generator] MoviePy loaded")
except ImportError as error:
    print(f"[video_generator] ERROR: MoviePy 2.x required: {error}")
    raise ImportError("Please install moviepy>=2.0.0") from error


def validate_image_file(path):
    """Check whether MoviePy can use a local image file."""
    return validate_image(path)


def _to_local_path(path):
    """Resolve stored web paths to absolute local filesystem paths."""
    if not path:
        return None

    if path.startswith("http://") or path.startswith("https://"):
        return None

    resolved = resolve_local_image_path(path)
    if resolved and os.path.exists(resolved):
        return resolved

    system_path = path.lstrip("/").replace("/", os.sep)
    absolute = os.path.join(Config.BASE_DIR, system_path)
    return absolute if os.path.exists(absolute) else None


def generate_video(image_urls, audio_paths, story_id, output_dir, audio_base_dir=None):
    """
    Create an MP4 slideshow synchronized to narration audio.
    Uses only validated local images from static/images/generated/.
    """
    print(f"[video_generator] Processing story: {story_id}")

    os.makedirs(output_dir, exist_ok=True)

    valid_image_paths = []
    skipped_images = []

    for path in image_urls or []:
        local_path = _to_local_path(path)
        if local_path and validate_image_file(local_path):
            valid_image_paths.append(local_path)
        else:
            skipped_images.append(path)
            print(f"[video_generator] Skipping invalid image: {path}")

    print(
        f"[video_generator] Images ready: {len(valid_image_paths)} valid, "
        f"{len(skipped_images)} skipped"
    )

    if not valid_image_paths:
        raise Exception(
            "Video generation failed: No valid local images found in static/images/generated/"
        )

    audio_clips = []
    video_clips = []
    final_audio = None
    final_video = None
    output_path = os.path.join(output_dir, f"{story_id}.mp4")

    try:
        for path in audio_paths or []:
            if os.path.exists(path):
                audio_clips.append(AudioFileClip(path))

        print(f"[video_generator] Audio clips loaded: {len(audio_clips)}")

        if not audio_clips:
            raise Exception("No valid audio files found for video.")

        final_audio = concatenate_audioclips(audio_clips)
        total_duration = final_audio.duration
        print(f"[video_generator] Audio duration: {total_duration:.2f}s")

        duration_per_image = total_duration / len(valid_image_paths)
        crossfade_duration = min(1.0, duration_per_image / 3)

        print(f"[video_generator] Creating {len(valid_image_paths)} clips at 854x480")
        for index, img_path in enumerate(valid_image_paths):
            try:
                # Load original size for logging
                with Image.open(img_path) as img:
                    img_w, img_h = img.size
                print(f"[INFO] Original image size: ({img_w}, {img_h})")
                print(f"[INFO] Target video frame size: (854, 480)")

                # Optimized resolution to 854x480 (480p) for much faster export
                clip = (
                    ImageClip(img_path)
                    .resized(height=480)
                    .with_duration(duration_per_image)
                )

                # 4. Zoom effects removed to ensure clear visibility

                video_clips.append(clip)
                print(f"[INFO] Video clip created for image {index}") # Added verification log
            except Exception as error:
                print(f"[video_generator] Clip error for {img_path}: {error}")

        if not video_clips:
            raise Exception("No video clips could be created from the provided images.")

        # Concatenate clips with overlap for slideshow functionality
        concatenated = concatenate_videoclips(
            video_clips, method="compose", padding=-crossfade_duration
        )

        # Safe export at 854x480 with ultrafast preset, optimized fps, and threading
        final_video = CompositeVideoClip(
            [concatenated.with_position("center")],
            size=(854, 480)
        ).with_audio(final_audio).with_duration(total_duration)

        print(f"[INFO] Final video size: 854x480 | Audio: {total_duration:.2f}s")
        print(f"[video_generator] Exporting to {output_path}")
        
        render_start = time.time()
        try:
            final_video.write_videofile(
                output_path,
                fps=12,
                preset="ultrafast",
                codec="libx264",
                audio_codec="aac",
                threads=4,
                logger=None,
            )
        except Exception as export_error:
            import traceback
            print(f"[ERROR] MoviePy export failed critically: {export_error}")
            print(traceback.format_exc())
            raise export_error
            
        render_end = time.time()
        print(f"[video_generator] Rendering completed in {render_end - render_start:.2f}s")
        print(f"[video_generator] Export complete: {output_path}")
        return output_path

    finally:
        if final_video:
            final_video.close()
        if final_audio:
            final_audio.close()
        for clip in video_clips:
            clip.close()
        for clip in audio_clips:
            clip.close()
