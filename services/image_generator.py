"""
Image Generation Service

Uses Pollinations AI to generate anime-style cultural illustrations.
Returns a direct URL — no local download required.
"""

import urllib.parse


def generate_image(prompt, story_id=None):
    """
    Generate a Pollinations AI illustration URL based on the story prompt.

    Args:
        prompt (str): Story title or scene description.
        story_id (str, optional): Reserved for future use.

    Returns:
        str: Pollinations AI image URL.
    """
    encoded = urllib.parse.quote(
        f"anime style Indian folklore illustration {prompt}"
    )

    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&width=1024&height=1024"
    )
