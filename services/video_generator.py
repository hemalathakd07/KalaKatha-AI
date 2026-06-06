import os
import requests
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, concatenate_audioclips

MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

def _download_image_with_retry(url, img_path, max_retries=MAX_RETRIES):
    """Download an image with retry logic and better error reporting."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return True
            else:
                last_error = f"HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            last_error = f"Timeout after {TIMEOUT_SECONDS}s (attempt {attempt+1}/{max_retries})"
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)[:100]} (attempt {attempt+1}/{max_retries})"
        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)[:100]} (attempt {attempt+1}/{max_retries})"
    
    return False, last_error

def generate_video(image_urls, audio_paths, story_id, output_dir, audio_base_dir):
    """
    Generates an animated slideshow video by syncing AI illustrations with narration.
    """
    # 1. Download images to local storage for processing
    temp_images = []
    download_errors = []
    
    for i, url in enumerate(image_urls):
        img_name = f"temp_{story_id}_{i}.jpg"
        img_path = os.path.join(output_dir, img_name)
        try:
            success, error_msg = _download_image_with_retry(url, img_path)
            if success:
                temp_images.append(img_path)
            else:
                download_errors.append(f"Image {i+1}: {error_msg}")
                print(f"[video_generator] Failed to download image {i+1}: {url}\nError: {error_msg}")
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            download_errors.append(f"Image {i+1}: {error_msg}")
            print(f"[video_generator] Unexpected error downloading image {i+1}: {str(e)}")

    if not temp_images:
        error_details = "\n".join(download_errors) if download_errors else "Unknown error"
        error_msg = f"No images available for video generation. All {len(image_urls)} image downloads failed.\n{error_details}"
        raise Exception(error_msg)

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
        duration_per_image = final_audio.duration / len(temp_images)
        
        for img_path in temp_images:
            # Create a clip for each image with specified duration
            clip = ImageClip(img_path).with_duration(duration_per_image)
            # Standardize to a common size (720p height) to prevent concatenation errors
            clip = clip.resized(height=720)
            video_clips.append(clip)

        # 4. Assemble and Export
        final_video = concatenate_videoclips(video_clips, method="compose").with_audio(final_audio)

        output_path = os.path.join(output_dir, f"{story_id}.mp4")
        
        # Export the final MP4
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac"
        )

    finally:
        # Explicitly close all clips to release memory and file handles
        if final_video: final_video.close()
        if final_audio: final_audio.close()
        for clip in audio_clips: clip.close()
        for clip in video_clips: clip.close()
        
        # Cleanup temp files
        for img_path in temp_images:
            if os.path.exists(img_path): os.remove(img_path)

    return output_path