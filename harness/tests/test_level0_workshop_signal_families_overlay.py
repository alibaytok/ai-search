import copy
import unittest

from harness.level0_workshop_signal_evidence import SIGNAL_FAMILIES
from harness.level0_workshop_signal_families_overlay import (
    SIGNAL_FAMILIES_OVERLAY_PATCH_KINDS,
    SignalFamiliesOverlayMalformedDelta,
    SignalFamiliesOverlayUnknownFamily,
    build_signal_families_overlay,
)


class SignalFamiliesOverlayBuilderTest(unittest.TestCase):
    def _delta(self):
        return {
            "patch_kind": "frame_b_canonical_addition",
            "canonical_additions": {
                "action.create": ["author"],
                "repo_meta_near_miss.repo_navigation": [
                    "what is this repository about",
                ],
            },
        }

    def test_patch_kind_enum_is_bounded(self):
        self.assertEqual(
            SIGNAL_FAMILIES_OVERLAY_PATCH_KINDS,
            ("frame_b_canonical_addition",),
        )

    def test_builds_immutable_overlay_without_mutating_base(self):
        before = copy.deepcopy(SIGNAL_FAMILIES)
        overlay = build_signal_families_overlay(SIGNAL_FAMILIES, self._delta())

        self.assertIsInstance(overlay, tuple)
        self.assertEqual(SIGNAL_FAMILIES, before)
        self.assertIsNot(overlay, SIGNAL_FAMILIES)

        action_create = next(
            family for family in overlay if family.family_id == "action.create"
        )
        self.assertIn("author", action_create.canonical_terms)
        self.assertIsInstance(action_create.canonical_terms, tuple)

        with self.assertRaises(AttributeError):
            overlay[0].canonical_terms.append("mutate")
        with self.assertRaises(TypeError):
            overlay[0] = overlay[0]

    def test_duplicate_addition_is_idempotent(self):
        overlay = build_signal_families_overlay(
            SIGNAL_FAMILIES,
            {
                "patch_kind": "frame_b_canonical_addition",
                "canonical_additions": {"action.create": ["create"]},
            },
        )
        action_create = next(
            family for family in overlay if family.family_id == "action.create"
        )
        self.assertEqual(action_create.canonical_terms.count("create"), 1)

    def test_unknown_family_rejected(self):
        with self.assertRaises(SignalFamiliesOverlayUnknownFamily):
            build_signal_families_overlay(
                SIGNAL_FAMILIES,
                {
                    "patch_kind": "frame_b_canonical_addition",
                    "canonical_additions": {"missing.family": ["author"]},
                },
            )

    def test_unknown_patch_kind_rejected(self):
        with self.assertRaises(SignalFamiliesOverlayMalformedDelta):
            build_signal_families_overlay(
                SIGNAL_FAMILIES,
                {
                    "patch_kind": "frame_b_logic_change",
                    "canonical_additions": {"action.create": ["author"]},
                },
            )

    def test_invalid_terms_rejected(self):
        bad_terms = ["Author", " author", ""]
        for term in bad_terms:
            with self.subTest(term=term):
                with self.assertRaises(SignalFamiliesOverlayMalformedDelta):
                    build_signal_families_overlay(
                        SIGNAL_FAMILIES,
                        {
                            "patch_kind": "frame_b_canonical_addition",
                            "canonical_additions": {"action.create": [term]},
                        },
                    )

    def test_non_ascii_term_rejected(self):
        with self.assertRaises(SignalFamiliesOverlayMalformedDelta):
            build_signal_families_overlay(
                SIGNAL_FAMILIES,
                {
                    "patch_kind": "frame_b_canonical_addition",
                    "canonical_additions": {"action.create": ["yard\u0131m"]},
                },
            )


if __name__ == "__main__":
    unittest.main()
