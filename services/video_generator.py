"""
Video Generation Service

Uses MoviePy to create a cinematic animated slideshow.
Features: Cinematic Pan/Zoom, Cross-fade transitions, Audio synchronization.
"""

import os
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
    Creates an MP4 video with cinematic effects (zoom/pan) synchronized to narration.
    Resolution: 1280x720 (HD).
    """
    print(f"[video_generator] Processing story: {story_id}")
    
    # 1. Resolve and Validate Local File Paths
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
        total_duration = final_audio.duration
        print(f"[video_generator] Audio duration: {total_duration}s")

        # 3. Create Cinematic Slideshow
        duration_per_image = total_duration / len(valid_image_paths)
        # Transition duration (seconds)
        crossfade = 1.0
        
        for i, img_path in enumerate(valid_image_paths):
            try:
                # Create clip with overlap for crossfade
                clip_duration = duration_per_image + (crossfade if i < len(valid_image_paths)-1 else 0)
                
                # Load image and resize to 1.2x to allow for zoom room
                clip = ImageClip(img_path).with_duration(clip_duration)
                
                # Apply Cinematic Zoom-in Effect (1.1 to 1.15 scale)
                clip = clip.resized(lambda t: 1.1 + 0.05 * (t / clip_duration))
                
                # Standardize to HD resolution
                clip = clip.cropped(width=1280, height=720, x_center=clip.w/2, y_center=clip.h/2)
                
                if i > 0:
                    # Smooth fade from previous scene
                    clip = clip.with_fadein(crossfade)
                
                video_clips.append(clip)
            except Exception as e:
                print(f"[video_generator] Clip error for {img_path}: {e}")

        # 4. Assemble and Synchronize
        final_video = concatenate_videoclips(video_clips, method="compose", padding=-crossfade).with_audio(final_audio)
        
        # Hard cap duration to audio length
        final_video = final_video.with_duration(total_duration)

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