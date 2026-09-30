"""Unit tests for the subject/community label resolvers."""

import pytest

from src.utils.create_system.community_resolver import community_folder
from src.utils.create_system.subject_resolver import resolve_collection


class TestResolveCollection:
    @pytest.mark.parametrize(
        ("label", "expected"),
        [
            ("Biología", "biology"),
            ("Química", "chemistry"),
            ("Historia del Arte", "arthistory"),
            ("Lengua Castellana y Literatura", "language"),
            ("Biology", "biology"),
            ("Art History", "arthistory"),
        ],
    )
    def test_resolves_localized_labels(self, label, expected):
        assert resolve_collection(label) == expected

    def test_unknown_label_is_slugified(self):
        assert resolve_collection("  Unknown Subject 42 ") == "unknownsubject42"

    def test_unknown_label_strips_accents_characters(self):
        # Accented characters are not in [a-z0-9] and are dropped by the slug fallback.
        assert resolve_collection("Ñoño") == "oo"


class TestCommunityFolder:
    @pytest.mark.parametrize(
        ("label", "expected"),
        [
            ("Andalucía", "Andalucia"),
            ("Islas Baleares", "Baleares"),
            ("Castilla-La Mancha", "CastillaLaMancha"),
            ("Comunidad Valenciana", "Valencia"),
        ],
    )
    def test_resolves_localized_labels(self, label, expected):
        assert community_folder(label) == expected

    def test_unknown_label_is_normalized_to_ascii_letters(self):
        assert community_folder("Región de Fantasía 3") == "RegiondeFantasia"
