"""
Image Generation Service

Uses Pollinations AI to generate anime-style cultural illustrations.
"""

import urllib.parse


def generate_image(prompt, story_id=None):
    """
    Generate an AI illustration URL based on the story prompt.

    Args:
        prompt (str): Story title or scene description.
        story_id (str, optional): Reserved for future local image storage.

    Returns:
        str: Pollinations AI image URL.
    """

    image_prompt = (
        f"Beautiful anime style Indian folklore illustration of {prompt}, "
        f"traditional village, vibrant colors, cinematic lighting"
    )

    encoded = urllib.parse.quote(image_prompt)

    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024"