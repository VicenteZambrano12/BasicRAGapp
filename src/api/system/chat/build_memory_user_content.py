"""Chat helper to pick what user content is stored in rolling memory."""


def build_memory_user_content(query: str, has_image: bool, intermediate_memory: str) -> str:
    """Choose memory payload using image context when present, else text query."""
    if has_image and intermediate_memory:
        return intermediate_memory
    if query:
        return query
    return ""
