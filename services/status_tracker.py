import time

# In-memory store for background task statuses
_statuses = {}

def update_status(story_id, status, error=None):
    """
    Update the status of a background story generation process.
    Stages: generating_story, generating_images, generating_audio, 
            generating_video, completed, failed
    """
    _statuses[story_id] = {
        "status": status,
        "error": str(error) if error else None,
        "last_update": time.time()
    }

def get_status(story_id):
    """Return the current status dict for a story."""
    return _statuses.get(story_id, {"status": "not_found"})