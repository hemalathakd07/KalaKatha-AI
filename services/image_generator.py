"""
Image Generation Service

Uses Pollinations AI (Flux model) to generate high-quality anime-style illustrations.
Implements robust error handling with retries and local disk caching.
"""

import os
import time
import requests
import shutil
from urllib.parse import quote_plus
from PIL import Image, ImageDraw, ImageFont

def ensure_fallback_exists(path):
    """Creates a local fallback image if missing."""
    if not os.path.exists(path):
        print(f"[image_generator] Creating placeholder fallback at {path}")
        img = Image.new('RGB', (1024, 1024), color=(40, 40, 40))
        d = ImageDraw.Draw(img)
        try:
            # Try to use a default font
            d.text((350, 500), "KalaKatha AI\nPlaceholder", fill=(255, 215, 0))
        except Exception:
            d.rectangle([300, 450, 700, 550], fill=(255, 215, 0))
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)

def validate_image(path):
    """Strict validation of image file integrity."""
    try:
        if not os.path.exists(path) or os.path.getsize(path) < 100:
            return False
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"[image_generator] Validation failed for {path}: {e}")
        return False

def generate_image(prompt, story_id, index, max_retries=3):
    """
    Generates an image from Pollinations AI, downloads it, and performs validation.
    Retries up to 3 times on failure.
    Returns the web-accessible path for the image.
    """
    # 1. Setup paths
    save_dir = os.path.join('static', 'images', 'generated')
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"{story_id}_{index}.jpg"
    local_path = os.path.join(save_dir, filename)
    web_path = f"/static/images/generated/{filename}"
    fallback_source = os.path.join('static', 'images', 'fallback.jpg')
    ensure_fallback_exists(fallback_source)

    # 2. Prepare Pollinations URL
    # We add quality boosters and specific style tags
    clean_prompt = f"masterpiece, anime style, highly detailed Indian folklore illustration, {prompt}, vibrant colors, cinematic lighting, 8k, sharp focus"
    encoded_prompt = quote_plus(clean_prompt)
    seed = 42 + index
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"

    # 3. Download
    for attempt in range(max_retries):
        try:
            print(f"[image_generator] Attempt {attempt+1} for scene {index}...")
            response = requests.get(url, timeout=40)
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                with open(local_path, "wb") as f:
                    f.write(response.content)
                
                if validate_image(local_path):
                    break # Success!
            print(f"[image_generator] Attempt {attempt+1} failed (Status: {response.status_code})")
        except Exception as e:
            print(f"[image_generator] Attempt {attempt+1} request failed: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2) # Wait before retry

    # 4. Final Validation & Fallback
    if validate_image(local_path):
        print(f"[image_generator] Success: {local_path}")
    else:
        print(f"[image_generator] Using fallback for {filename}")
        try:
            shutil.copy(fallback_source, local_path)
        except Exception as fe:
            print(f"[image_generator] CRITICAL: Fallback copy failed: {fe}")
            # Create a very emergency black square if even copy fails
            black_img = Image.new('RGB', (1024, 1024), color='black')
            black_img.save(local_path)

    return web_path