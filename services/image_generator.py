"""
Image Generation Service
Primary: Hugging Face hf-inference (FLUX.1-schnell).
Downloads and validates images locally before returning web paths.
"""
import base64
import json
import os
import shutil
import time
import traceback

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw

from config import Config

load_dotenv()

HUGGINGFACE_API_KEY = (os.getenv("HUGGINGFACE_API_KEY") or "").strip()
HF_FLUX_MODEL = "black-forest-labs/FLUX.1-schnell"
HF_FLUX_URL = f"https://router.huggingface.co/hf-inference/models/{HF_FLUX_MODEL}"
HF_REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "image/png",
}
PROMPT_TEMPLATE = (
    "Studio Ghibli style Indian folklore illustration, anime masterpiece, "
    "cinematic lighting, detailed characters, traditional Indian village, "
    "vibrant colors, highly detailed artwork, {scene_description}"
)


def _hf_api_key():
    """Return the configured Hugging Face API key (never log the value)."""
    return (os.getenv("HUGGINGFACE_API_KEY") or HUGGINGFACE_API_KEY or "").strip()


def _log_hf_token_status():
    present = bool(_hf_api_key())
    print(f"[INFO] HUGGINGFACE_API_KEY present: {present}")
    if not present:
        print("[INFO] Set HUGGINGFACE_API_KEY in .env with Inference Providers permission.")
    return present


def _generated_dir():
    path = Config.GENERATED_IMAGES_DIR
    os.makedirs(path, exist_ok=True)
    return path


def _fallback_path():
    path = os.path.join(Config.BASE_DIR, "static", "images", "fallback.jpg")
    ensure_fallback_exists(path)
    return path


def ensure_fallback_exists(path=None):
    """Create a local fallback placeholder image if missing."""
    path = path or _fallback_path()
    if os.path.exists(path) and os.path.getsize(path) > 100:
        return path
    print(f"[INFO] Creating fallback placeholder at {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new("RGB", (1024, 1024), color=(40, 40, 40))
    draw = ImageDraw.Draw(img)
    try:
        draw.text((280, 480), "KalaKatha AI Placeholder", fill=(255, 215, 0))
    except Exception:
        draw.rectangle([300, 450, 700, 550], fill=(255, 215, 0))
    img.save(path, "JPEG", quality=90)
    return path


def build_image_prompt(scene_description):
    """Wrap a scene description in the quality prompt template."""
    return PROMPT_TEMPLATE.format(scene_description=scene_description.strip())


def image_filename(story_id, index):
    """Standard local filename for a story scene image."""
    return f"{story_id}_scene_{index}.jpg"


def local_image_path(story_id, index):
    """Absolute filesystem path for a scene image."""
    return os.path.join(_generated_dir(), image_filename(story_id, index))


def web_image_path(story_id, index):
    """Browser-accessible path stored in stories.json."""
    return f"/static/images/generated/{image_filename(story_id, index)}"


def validate_image(path):
    """Validate file exists, has content, and is a readable PNG/JPG image."""
    try:
        if not path or not os.path.exists(path) or os.path.getsize(path) <= 0:
            return False
        with Image.open(path) as img:
            if img.format not in ("PNG", "JPEG", "JPG"):
                print(f"[ERROR] Unsupported image format: {img.format}")
                return False
            img.verify()
        with Image.open(path) as img:
            img.load()
        return True
    except Exception as error:
        print(f"[ERROR] Image validation failed for {path}: {error}")
        return False


def _content_type_is_image(content_type):
    lowered = (content_type or "").lower()
    return lowered.startswith("image/") and "html" not in lowered


def _looks_like_image_bytes(content):
    if not content or len(content) < 100:
        return False
    return content[:4] in (b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"RIFF")


def _save_image_bytes(content, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as handle:
        handle.write(content)
    print(f"[INFO] Image saved: {filepath}")


def _log_response_details(response, url):
    """Log HTTP response metadata for debugging provider failures."""
    print(f"[INFO] Request URL: {url}")
    print(f"[INFO] Response status: {response.status_code}")
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "application/json" in content_type and response.content:
        try:
            body_preview = response.json()
            if isinstance(body_preview, dict):
                body_preview = {key: body_preview[key] for key in list(body_preview)[:6]}
            print(f"[INFO] Response JSON preview: {body_preview}")
        except (json.JSONDecodeError, ValueError):
            preview = response.content[:300].decode("utf-8", errors="replace")
            print(f"[INFO] Response body preview: {preview}")


def _download_image_from_url(url):
    """Download image bytes from a provider-returned URL."""
    print(f"[INFO] Downloading image from provider URL: {url}")
    try:
        response = requests.get(url, timeout=120)
        print(f"[INFO] Response status: {response.status_code}")
        if response.status_code == 200 and _looks_like_image_bytes(response.content):
            return response.content
    except requests.RequestException as error:
        print(f"[ERROR] Provider image URL download failed: {error}")
        print(traceback.format_exc())
    return None


def _extract_image_bytes_from_response(response):
    """Return raw image bytes from a Hugging Face response (binary or JSON wrapper)."""
    content_type = (response.headers.get("Content-Type") or "").lower()
    if _looks_like_image_bytes(response.content):
        return response.content
    if _content_type_is_image(content_type) and response.content:
        return response.content
    if "application/json" not in content_type or not response.content:
        return None
    try:
        payload = response.json()
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(payload, str):
        if payload.startswith("http://") or payload.startswith("https://"):
            return _download_image_from_url(payload)
        try:
            return base64.b64decode(payload)
        except (ValueError, TypeError):
            return None
    if not isinstance(payload, dict):
        return None
    for key in ("image", "output", "result"):
        value = payload.get(key)
        if isinstance(value, str):
            if value.startswith("http://") or value.startswith("https://"):
                return _download_image_from_url(value)
            try:
                return base64.b64decode(value)
            except (ValueError, TypeError):
                continue
    for key in ("images", "outputs", "data"):
        items = payload.get(key)
        if not isinstance(items, list) or not items:
            continue
        first = items[0]
        if isinstance(first, str):
            if first.startswith("http://") or first.startswith("https://"):
                return _download_image_from_url(first)
            try:
                return base64.b64decode(first)
            except (ValueError, TypeError):
                continue
        if isinstance(first, dict):
            for nested_key in ("url", "image", "b64_json", "content"):
                nested = first.get(nested_key)
                if isinstance(nested, str):
                    if nested.startswith("http://") or nested.startswith("https://"):
                        return _download_image_from_url(nested)
                    if nested_key == "b64_json":
                        try:
                            return base64.b64decode(nested)
                        except (ValueError, TypeError):
                            continue
    return None


def _request_huggingface_image(prompt, filepath, api_key, attempt):
    """POST to hf-inference FLUX.1-schnell and save returned image bytes."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        **HF_REQUEST_HEADERS,
    }
    payload = {"inputs": prompt}
    print("[INFO] Sending request to Hugging Face...")
    print(f"[INFO] Request URL: {HF_FLUX_URL}")
    try:
        response = requests.post(
            HF_FLUX_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )
        print(f"[INFO] Response status: {response.status_code}")
        if response.status_code not in (200, 201):
            _log_response_details(response, HF_FLUX_URL)
        if response.status_code in (503, 504):
            wait = 5 * attempt
            print(f"[INFO] HF model loading ({response.status_code}); waiting {wait}s...")
            time.sleep(wait)
            return False
        image_bytes = _extract_image_bytes_from_response(response)
        if not image_bytes or not _looks_like_image_bytes(image_bytes):
            print(
                f"[ERROR] Hugging Face returned no valid image bytes: "
                f"status={response.status_code}"
            )
            return False
        _save_image_bytes(image_bytes, filepath)
        if validate_image(filepath):
            return True
        print(f"[ERROR] Saved image failed validation: {filepath}")
    except requests.RequestException as error:
        print(f"[ERROR] Hugging Face request failed: {error}")
        print(traceback.format_exc())
    return False


def _generate_via_huggingface(prompt, filepath, max_retries=3):
    """Generate an image via Hugging Face with retries for transient failures."""
    api_key = _hf_api_key()
    _log_hf_token_status()
    if not api_key:
        print("[ERROR] HUGGINGFACE_API_KEY not set; cannot generate image.")
        return False
    for attempt in range(1, max_retries + 1):
        if _request_huggingface_image(prompt, filepath, api_key, attempt):
            return True
        if attempt < max_retries:
            time.sleep(3 * attempt)
    print("[ERROR] Hugging Face FLUX generation failed after all retries.")
    return False


def _apply_fallback(filepath):
    fallback = _fallback_path()
    try:
        shutil.copy(fallback, filepath)
        print(f"[ERROR] Image generation failed; using fallback for {os.path.basename(filepath)}")
        return validate_image(filepath)
    except Exception as error:
        print(f"[ERROR] Fallback copy failed: {error}")
        print(traceback.format_exc())
        return False


def generate_image(prompt, story_id, index, max_retries=3, allow_fallback=True):
    """
    Generate one scene image via Hugging Face FLUX, save locally, return web path.
    Falls back to fallback.jpg only when allow_fallback=True and HF fails.
    """
    filepath = local_image_path(story_id, index)
    web_path = web_image_path(story_id, index)
    if validate_image(filepath):
        print(f"[INFO] Using cached image: {filepath}")
        return web_path
    full_prompt = build_image_prompt(prompt)
    print(f"[PROMPT LOG] Scene {index}: {full_prompt}")
    print(f"[INFO] Generating image: scene {index} for story {story_id}")
    if _generate_via_huggingface(full_prompt, filepath, max_retries=max_retries):
        return web_path
    if allow_fallback:
        _apply_fallback(filepath)
        return web_path
    print(f"[ERROR] Image generation failed for scene {index}")
    return None


def generate_scene_images(story_id, scene_prompts, allow_fallback=True):
    """Generate unique images for each scene prompt."""
    image_urls = []
    for index, scene_prompt in enumerate(scene_prompts):
        try:
            url = generate_image(
                scene_prompt,
                story_id=story_id,
                index=index,
                allow_fallback=allow_fallback,
            )
            if url:
                image_urls.append(url)
        except Exception as error:
            print(f"[ERROR] Image generation failed: {error}")
            print(traceback.format_exc())
    return image_urls


def resolve_local_image_path(web_or_local_path):
    """Convert a stored /static/... path to an absolute local path."""
    if not web_or_local_path:
        return None
    if web_or_local_path.startswith("http://") or web_or_local_path.startswith("https://"):
        return None
    relative = web_or_local_path.lstrip("/").replace("/", os.sep)
    basename = os.path.basename(relative)
    generated_dir = _generated_dir()
    candidates = [
        os.path.join(Config.BASE_DIR, relative),
        os.path.join(generated_dir, basename),
    ]
    # Support legacy filenames like {story_id}_0.jpg
    if "_scene_" not in basename and basename.endswith(".jpg"):
        parts = basename.rsplit("_", 1)
        if len(parts) == 2 and parts[1].replace(".jpg", "").isdigit():
            candidates.insert(0, os.path.join(generated_dir, basename))
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


def is_valid_local_image(web_or_local_path):
    """Check whether a stored image path points to a valid local file."""
    local_path = resolve_local_image_path(web_or_local_path)
    return validate_image(local_path) if local_path else False
