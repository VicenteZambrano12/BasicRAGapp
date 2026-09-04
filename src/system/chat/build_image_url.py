"""Chat helper to normalize URL/base64 image inputs."""

import logging
from fastapi import HTTPException


logger = logging.getLogger(__name__)


def build_image_url(image_data: str, image_type: str) -> str:
    """Convert image payload into a model-ready URL or data URL string."""
    if image_type == "base64":
        base64_data = image_data
        mime_type = "image/jpeg"

        if base64_data.startswith("data:"):
            header_part = base64_data.split(",")[0]
            mime_part = header_part.split(";")[0].replace("data:", "")
            if mime_part.startswith("image/"):
                mime_type = mime_part
            base64_data = base64_data.split(",")[1]
            logger.info(f"[CHAT] Extracted MIME type: {mime_type}")
        else:
            if base64_data.startswith("iVBORw0KGgo"):
                mime_type = "image/png"
            elif base64_data.startswith("/9j/"):
                mime_type = "image/jpeg"
            elif base64_data.startswith("R0lGODlh"):
                mime_type = "image/gif"
            elif base64_data.startswith("UklGR"):
                mime_type = "image/webp"
            logger.info(f"[CHAT] Detected MIME type: {mime_type}")

        return f"data:{mime_type};base64,{base64_data}"

    if image_type == "url":
        if not (image_data.startswith("http://") or image_data.startswith("https://")):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        return image_data

    raise HTTPException(status_code=400, detail=f"Unknown image_type: {image_type}")
