"""Maps a localized community label (as exposed by GET /config) to its prompts/ folder name."""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _load_community_label_to_folder() -> dict:
    """Build a community label -> prompts/ folder mapping from the localized configs."""
    mapping = {}
    for filename in ("es.config.json", "en.config.json"):
        path = CONFIG_DIR / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("community_map", {}).values():
            mapping[entry["label"]] = entry["folder"]
    return mapping


_COMMUNITY_LABEL_TO_FOLDER: Optional[dict] = None


def community_folder(community: str) -> str:
    """Resolve a community label to its prompts/ folder name."""
    global _COMMUNITY_LABEL_TO_FOLDER
    if _COMMUNITY_LABEL_TO_FOLDER is None:
        _COMMUNITY_LABEL_TO_FOLDER = _load_community_label_to_folder()

    folder = _COMMUNITY_LABEL_TO_FOLDER.get(community)
    if folder:
        return folder

    logger.warning(f"[CREATE_SYSTEM] Unknown community label '{community}', deriving folder name")
    normalized = unicodedata.normalize("NFKD", community).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z]", "", normalized)
