import os
import logging
from PIL import Image

try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
    import moviepy.video.fx as vfx
    print(f"[video_generator] MoviePy loaded")
except ImportError as e:
    print(f"[video_generator] ERROR: MoviePy 2.x required: {e}")
    raise ImportError("Please install moviepy>=2.0.0")

def validate_image_file(path):
    """Checks if an image is actually loadable by MoviePy."""
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except:
        return False

def generate_video(image_urls, audio_paths, story_id, output_dir, audio_base_dir):
    """
    Generates an animated slideshow video using locally saved images.
    Compatible with MoviePy 2.x.
    """
    print(f"[video_generator] Processing story: {story_id}")
    
    # 1. Resolve local file paths
    valid_image_paths = []
    for path in image_urls:
        # Convert web path (/static/...) to system path (static/...)
        system_path = path.lstrip('/')
        if os.path.exists(system_path) and validate_image_file(system_path):
            valid_image_paths.append(system_path)
        else:
            print(f"[video_generator] Skipping invalid image: {system_path}")

    if not valid_image_paths:
        raise Exception("Video generation failed: No local images found in static/images/generated/")

    # 2. Process Audio and Video Clips
    audio_clips = []
    video_clips = []
    final_audio = None
    final_video = None
    output_path = os.path.join(output_dir, f"{story_id}.mp4")
    
    try:
        for path in audio_paths:
            if os.path.exists(path):
                audio_clips.append(AudioFileClip(path))
        
        if not audio_clips:
            raise Exception("No valid audio files found for video.")
        
        final_audio = concatenate_audioclips(audio_clips)
        print(f"[video_generator] Audio duration: {final_audio.duration}s")

        # 3. Create Video Slideshow
        duration_per_image = final_audio.duration / len(valid_image_paths)
        
        for img_path in valid_image_paths:
            try:
                # MoviePy 2.x uses .with_duration()
                clip = ImageClip(img_path).with_duration(duration_per_image)
                # Standardize height to 720p for consistency
                clip = clip.resized(height=720)
                video_clips.append(clip)
            except Exception as e:
                print(f"[video_generator] Clip error for {img_path}: {e}")

        # 4. Assemble and Export
        final_video = concatenate_videoclips(video_clips, method="compose").with_audio(final_audio)

        print(f"[video_generator] Exporting to {output_path}")
        final_video.write_videofile(
            output_path, 
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None, # Suppress MoviePy verbose output
        )
        return output_path

    finally:
        # Clean up resources
        if final_video: final_video.close()
        if final_audio: final_audio.close()
        for clip in video_clips:
            clip.close()