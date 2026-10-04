"""Unit tests for src.i18n."""

import pytest

from src.i18n import get_language, get_language_instruction, translate


def test_defaults_to_spanish():
    assert get_language()["language_instruction"] == "Responde siempre en español."


@pytest.mark.parametrize("language", ["EN", "en", "En"])
def test_language_lookup_is_case_insensitive(language):
    assert get_language(language)["language_instruction"] == "Always respond in English."


@pytest.mark.parametrize("language", ["FR", "", None, "es-ES"])
def test_unsupported_language_falls_back_to_spanish(language):
    assert get_language(language) == get_language("ES")


def test_language_instruction_differs_per_language():
    assert get_language_instruction("ES") != get_language_instruction("EN")


def test_translate_interpolates_values():
    assert translate("welcome", "ES", subject="Biología") == (
        "¡Hola! ¿Cómo puedo ayudarte a estudiar tu examen de Biología?"
    )
    assert translate("welcome", "EN", subject="Biology") == (
        "Hello! How can I help you study for your Biology exam?"
    )


def test_translate_raises_for_unknown_key():
    with pytest.raises(KeyError):
        translate("does_not_exist", "ES")
