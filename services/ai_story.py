"""
AI Story Generation Service

This module handles cultural story generation from user prompts.
Currently returns dummy stories — replace with Gemini API later.
"""


def generate_story(prompt):
    """
    Generate a cultural folk tale based on the user's prompt.

    Args:
        prompt (str): Story title or theme provided by the user.

    Returns:
        str: Generated story text.

    TODO:
        - Integrate Google Gemini API for real story generation
        - Add regional language support
        - Include cultural context from a knowledge base
    """
    dummy_story = f"""Long ago, in a village nestled between emerald hills and a winding river, the elders spoke of "{prompt}" — a tale passed down through generations around crackling fires and monsoon evenings.

In those days, a young storyteller named Ananya discovered an ancient scroll hidden beneath the roots of a banyan tree. The scroll spoke of courage, community, and the wisdom hidden in everyday traditions. Inspired, she gathered the village children and began to weave the legend anew.

As the story unfolded, the children saw themselves in its heroes — brave enough to question, wise enough to listen, and kind enough to carry their culture forward. The tale of "{prompt}" reminded everyone that heritage is not a relic of the past, but a living flame that grows brighter with each telling.

And so, the village learned that every story saved is a bridge between ancestors and those yet to come. The banyan tree still stands today, its shade a sanctuary where new voices add chapters to the eternal narrative of "{prompt}."

[This is a placeholder story. Connect the Gemini API in ai_story.py to generate authentic, culturally rich narratives.]"""

    return dummy_story
