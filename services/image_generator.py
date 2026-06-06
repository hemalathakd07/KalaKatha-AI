"""
Image Generation Service

Uses Pollinations AI to generate anime-style cultural illustrations.
Downloads images locally and caches them with retry logic.
"""

import hashlib
import os
import re
import urllib.parse
import requests

FALLBACK_IMAGE_URL = "/static/images/placeholder.svg"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30


def _clean_prompt(prompt):
    """Normalize user prompt for safer Pollinations requests."""
    cleaned = re.sub(r"\s+", " ", (prompt or "").strip())
    return cleaned[:240] if cleaned else "Indian folklore scene"


def _seed_from_story_id(story_id):
    """Create a stable numeric seed from a story ID."""
    if not story_id:
        return None

    digest = hashlib.md5(story_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def build_pollinations_url(prompt, story_id=None, index=0):
    """
    Build a Pollinations URL with flux model.

    Args:
        prompt (str): Scene description.
        story_id (str, optional): Used for deterministic seed generation.
        index (int): Scene index to ensure different seeds for different scenes.

    Returns:
        str: Pollinations image URL.
    """
    cleaned_prompt = _clean_prompt(prompt)
    image_prompt = (
        "anime style Indian folklore illustration, "
        f"{cleaned_prompt}, vibrant colors, cinematic lighting, high detail"
    )
    encoded = urllib.parse.quote(image_prompt)

    params = ["model=flux", "width=1024", "height=1024", "nologo=true"]
    seed = _seed_from_story_id(story_id)

    if seed is not None:
        params.append(f"seed={seed + index}")

    return f"{POLLINATIONS_BASE}{encoded}?{'&'.join(params)}"


def _download_image_with_retry(url, save_path, max_retries=MAX_RETRIES):
    """Download an image with retry logic."""
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        if chunk:
                            f.write(chunk)
                return True, None
            else:
                last_error = f"HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            last_error = f"Timeout after {TIMEOUT_SECONDS}s (attempt {attempt+1}/{max_retries})"
        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)[:100]} (attempt {attempt+1}/{max_retries})"
        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)[:100]} (attempt {attempt+1}/{max_retries})"
    
    return False, last_error


def generate_image(prompt, story_id=None, index=0, output_dir=None):
    """
    Generate and download an image from Pollinations AI.
    
    Args:
        prompt (str): Scene description.
        story_id (str, optional): Story identifier for seed generation.
        index (int): Scene index.
        output_dir (str, optional): Directory to save the image. If None, returns Pollinations URL.
    
    Returns:
        str: Local file URL if output_dir provided and download succeeds, else Pollinations URL.
    """
    image_url = build_pollinations_url(prompt, story_id, index)
    
    if not output_dir:
        return image_url
    
    try:
        filename = f"{story_id}_{index}.jpg"
        save_path = os.path.join(output_dir, filename)
        
        success, error_msg = _download_image_with_retry(image_url, save_path)
        if success:
            return f"/static/images/generated/{filename}"
        else:
            print(f"[image_generator] Failed to download image {index}: {error_msg}")
            return image_url
    except Exception as e:
        print(f"[image_generator] Unexpected error generating image {index}: {str(e)}")
        return image_url