import os
import requests
import logging

try:
    import moviepy
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
    print("MoviePy loaded successfully")
    print("MoviePy version:", moviepy.__version__)
except ImportError as e:
    print(f"ERROR: MoviePy not installed or incompatible version found: {e}")
    raise

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow (PIL) not installed. Run 'pip install Pillow'")
    raise

MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

def generate_video(image_urls, audio_paths, story_id, output_dir, audio_base_dir):
    """
    Generates an animated slideshow video using locally saved images.
    Compatible with MoviePy 2.x.
    """
    # 1. Resolve local file paths
    valid_image_paths = []
    for path in image_urls:
        # Convert web path (/static/...) to system path (static/...)
        system_path = path.lstrip('/')
        if os.path.exists(system_path):
            valid_image_paths.append(system_path)
            print("[IMAGE FOUND]", system_path)
        else:
            print(f"[IMAGE MISSING] WARNING: {system_path}")

    if not valid_image_paths:
        raise Exception("Video generation failed: No local images found in static/images/generated/")

    print(f"[video_generator] Total images used for generation: {len(valid_image_paths)}")
    print(f"[video_generator] Starting assembly for story: {story_id}")

    # 2. Process Audio and Video Clips
    audio_clips = []
    video_clips = []
    final_audio = None
    final_video = None
    
    try:
        for path in audio_paths:
            if os.path.exists(path):
                audio_clips.append(AudioFileClip(path))
        
        if not audio_clips:
            raise Exception("Narration files not found.")
        
        final_audio = concatenate_audioclips(audio_clips)

        # 3. Create Video Slideshow
        # Calculate duration per image so the total video matches audio length
        duration_per_image = final_audio.duration / len(valid_image_paths)
        
        for img_path in valid_image_paths:
            # Create a clip for each image with specified duration
            clip = ImageClip(img_path).with_duration(duration_per_image)
            # Standardize to a common size (720p height) to prevent concatenation errors
            clip = clip.resize(height=720) # Changed from .resized() to .resize() for MoviePy 2.x
            video_clips.append(clip)

        # 4. Assemble and Export
        final_video = concatenate_videoclips(video_clips, method="compose").with_audio(final_audio)

        output_path = os.path.join(output_dir, f"{story_id}.mp4")
        
        # Export the final MP4
        final_video.write_videofile(
            output_path, 
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None, # Suppress MoviePy verbose output
        )
        return output_path # Return the path for app.py to use

    finally:
        # Clean up resources
        if final_video:
            final_video.close()
        if final_audio:
            final_audio.close()
        for clip in video_clips:
            clip.close()