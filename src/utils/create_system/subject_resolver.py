"""Resolves a localized subject label (e.g. 'Biología'/'Biology') to its Qdrant collection name."""

import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _load_subject_label_to_collection() -> dict:
    """Build a subject label -> Qdrant collection mapping from the localized configs."""
    mapping = {}
    for filename in ("es.config.json", "en.config.json"):
        path = CONFIG_DIR / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        for entry in data.get("subject_map", {}).values():
            mapping[entry["label"]] = entry["collection"]
    return mapping


_SUBJECT_LABEL_TO_COLLECTION: Optional[dict] = None


def resolve_collection(subject: str) -> str:
    """Resolve a subject label to its Qdrant collection name."""
    global _SUBJECT_LABEL_TO_COLLECTION
    if _SUBJECT_LABEL_TO_COLLECTION is None:
        _SUBJECT_LABEL_TO_COLLECTION = _load_subject_label_to_collection()

    collection = _SUBJECT_LABEL_TO_COLLECTION.get(subject)
    if collection:
        return collection

    # Fallback for an unrecognized subject: normalize into a collection-like slug.
    logger.warning(f"[CREATE_SYSTEM] Unknown subject label '{subject}', deriving collection slug")
    return re.sub(r"[^a-z0-9]+", "", subject.strip().lower())
