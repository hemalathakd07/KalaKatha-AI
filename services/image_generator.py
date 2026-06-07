import os
import requests
import shutil
from urllib.parse import quote
from PIL import Image

def generate_image(prompt, story_id, index):
    """
    Generates an image from Pollinations AI, downloads it, and performs validation.
    If downloading or validation fails, it substitutes a fallback image.
    Returns the web-accessible path for the image.
    """
    # 1. Setup paths
    save_dir = os.path.join('static', 'images', 'generated')
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"{story_id}_{index}.jpg"
    local_path = os.path.join(save_dir, filename)
    web_path = f"/static/images/generated/{filename}"
    fallback_source = os.path.join('static', 'images', 'fallback.jpg')

    # 2. Prepare Pollinations URL
    clean_prompt = f"anime style Indian folklore illustration, {prompt}, vibrant colors, cinematic lighting, high detail"
    encoded_prompt = quote(clean_prompt)
    seed = 42 + index
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width=1024&height=1024&nologo=true&seed={seed}"

    image_is_valid = False

    # 3. Download and HTTP level validation
    try:
        response = requests.get(url, timeout=30)
        content_type = response.headers.get("Content-Type", "")
        
        if response.status_code == 200 and content_type.startswith("image/"):
            with open(local_path, "wb") as f:
                f.write(response.content)
            
            # 4. Content validation using Pillow
            try:
                with Image.open(local_path) as img:
                    img.verify()
                image_is_valid = True
            except Exception:
                # File saved but Pillow verification failed (corrupt image)
                pass
        else:
            print(f"Pollinations returned non-image response: Status {response.status_code}, Type {content_type}")
            if response.text:
                print(f"Response text: {response.text[:500]}")
    except Exception as e:
        print(f"Download error: {e}")

    # 5. Handle fallback if invalid or download failed
    if not image_is_valid:
        if os.path.exists(fallback_source):
            try:
                shutil.copy(fallback_source, local_path)
                print(f"Invalid image replaced with fallback: {local_path}")
            except Exception as fe:
                print(f"Error copying fallback: {fe}")
        else:
            print(f"[image_generator] CRITICAL: Fallback file missing at {fallback_source}")
    else:
        print(f"Saved image: {local_path}")

    return web_path