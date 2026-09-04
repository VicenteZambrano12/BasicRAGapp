"""Backend internationalization helpers."""

from importlib import import_module
from typing import Mapping

DEFAULT_LANGUAGE = "ES"
SUPPORTED_LANGUAGES = frozenset({"ES", "EN"})


def get_language(language: str = DEFAULT_LANGUAGE) -> Mapping[str, str]:
    """Return the dictionary for a supported language, falling back to Spanish."""
    normalized_language = (language or DEFAULT_LANGUAGE).upper()
    if normalized_language not in SUPPORTED_LANGUAGES:
        normalized_language = DEFAULT_LANGUAGE

    module = import_module(f"src.i18n.languages.{normalized_language.lower()}")
    return module.TRANSLATIONS


def get_language_instruction(language: str = DEFAULT_LANGUAGE) -> str:
    """Return the instruction that makes the model answer in the selected language."""
    return get_language(language)["language_instruction"]


def translate(key: str, language: str = DEFAULT_LANGUAGE, **values: str) -> str:
    """Translate a key and format its optional values."""
    return get_language(language)[key].format(**values)
