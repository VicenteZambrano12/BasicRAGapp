"""Maps a localized community label (as exposed by GET /config) to its prompts/ folder name."""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

_COMMUNITY_FOLDERS = {
    "Andalucía": "Andalucia",
    "Andalusia": "Andalucia",
    "Aragón": "Aragon",
    "Aragon": "Aragon",
    "Asturias": "Asturias",
    "Islas Baleares": "Baleares",
    "Balearic Islands": "Baleares",
    "Canarias": "Canarias",
    "Canary Islands": "Canarias",
    "Cantabria": "Cantabria",
    "Castilla-La Mancha": "CastillaLaMancha",
    "Castile-La Mancha": "CastillaLaMancha",
    "Castilla y León": "CastillaLeon",
    "Castile and Leon": "CastillaLeon",
    "Cataluña": "Cataluna",
    "Catalonia": "Cataluna",
    "Extremadura": "Extremadura",
    "Galicia": "Galicia",
    "La Rioja": "LaRioja",
    "Comunidad de Madrid": "Madrid",
    "Community of Madrid": "Madrid",
    "Región de Murcia": "Murcia",
    "Region of Murcia": "Murcia",
    "Comunidad Foral de Navarra": "Navarra",
    "Chartered Community of Navarre": "Navarra",
    "País Vasco": "PaisVasco",
    "Basque Country": "PaisVasco",
    "Comunidad Valenciana": "Valencia",
    "Valencian Community": "Valencia",
}


def community_folder(community: str) -> str:
    """Resolve a community label to its prompts/ folder name."""
    folder = _COMMUNITY_FOLDERS.get(community)
    if folder:
        return folder

    logger.warning(f"[CREATE_SYSTEM] Unknown community label '{community}', deriving folder name")
    normalized = unicodedata.normalize("NFKD", community).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z]", "", normalized)
