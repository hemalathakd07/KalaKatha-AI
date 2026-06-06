"""
Image Generation Service

Uses Pollinations AI to generate anime-style cultural illustrations.
Returns direct URLs with stable seeds and a local fallback placeholder.
"""

import hashlib
import re
import urllib.parse

FALLBACK_IMAGE_URL = "/static/images/placeholder.svg"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


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


def build_pollinations_url(prompt, story_id=None, attempt=0):
    """
    Build a Pollinations URL with flux model and retry-safe seed offset.

    Args:
        prompt (str): Story title or scene description.
        story_id (str, optional): Used for deterministic seed generation.
        attempt (int): Retry attempt number for seed offset.

    Returns:
        str: Pollinations image URL.
    """
    cleaned_prompt = _clean_prompt(prompt)
    image_prompt = (
        "anime style Indian folklore illustration, "
        f"{cleaned_prompt}, traditional village, vibrant colors, cinematic lighting"
    )
    encoded = urllib.parse.quote(image_prompt)

    params = ["model=flux", "width=1024", "height=1024", "nologo=true"]
    seed = _seed_from_story_id(story_id)

    if seed is not None:
        params.append(f"seed={seed + attempt}")

    return f"{POLLINATIONS_BASE}{encoded}?{'&'.join(params)}"


def get_fallback_image_url():
    """Return the static placeholder used when remote generation fails."""
    return FALLBACK_IMAGE_URL


def generate_image(prompt, story_id=None):
    try:
        encoded = urllib.parse.quote(
            f"anime style Indian folklore illustration {prompt}"
        )

        return (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width=1024&height=1024"
        )

    except Exception:
        return "/static/images/fallback.jpg"