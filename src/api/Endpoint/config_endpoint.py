"""Endpoint for localized study configuration options."""

import json
from pathlib import Path
from typing import Dict, List, Literal, Union

from fastapi import APIRouter, HTTPException


router = APIRouter()
CONFIG_DIRECTORY = Path(__file__).resolve().parents[2] / "config"


@router.get(
    "/config",
    response_model=Dict[str, Union[List[str], Dict[str, Dict[str, str]]]],
    summary="Get study configuration",
    description=(
        "Return the available autonomous communities and subjects for the "
        "requested language."
    ),
    response_description="Localized study configuration options.",
)
async def get_config(
    language: Literal["ES", "EN"] = "ES",
) -> Dict[str, Union[List[str], Dict[str, Dict[str, str]]]]:
    """Return autonomous communities and subjects for the requested language."""

    config_path = CONFIG_DIRECTORY / f"{language.lower()}.config.json"
    try:
        with config_path.open(encoding="utf-8") as config_file:
            return json.load(config_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to load localized study configuration.",
        ) from exc
