"""Tests for the WCAG contrast arithmetic."""

import os
import sys
import unittest

SKILL_SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skill",
    "scripts",
)
sys.path.insert(0, SKILL_SCRIPTS)

import contrast  # noqa: E402


class TestParseColor(unittest.TestCase):
    def test_six_digit_hex(self):
        self.assertEqual(contrast.parse_color("#ffffff"), (255.0, 255.0, 255.0, 1.0))

    def test_three_digit_hex_expands(self):
        self.assertEqual(contrast.parse_color("#fff"), (255.0, 255.0, 255.0, 1.0))

    def test_eight_digit_hex_carries_alpha(self):
        color = contrast.parse_color("#00000080")
        self.assertEqual(color[0:3], (0.0, 0.0, 0.0))
        self.assertAlmostEqual(color[3], 128 / 255.0, places=4)

    def test_rgb_function(self):
        self.assertEqual(contrast.parse_color("rgb(255, 0, 0)"), (255.0, 0.0, 0.0, 1.0))

    def test_rgb_space_separated_with_slash_alpha(self):
        color = contrast.parse_color("rgb(0 0 0 / 50%)")
        self.assertAlmostEqual(color[3], 0.5, places=4)

    def test_hsl_function(self):
        color = contrast.parse_color("hsl(0, 100%, 50%)")
        self.assertAlmostEqual(color[0], 255.0, places=3)
        self.assertAlmostEqual(color[1], 0.0, places=3)
        self.assertAlmostEqual(color[2], 0.0, places=3)

    def test_named_color(self):
        self.assertEqual(contrast.parse_color("white"), (255.0, 255.0, 255.0, 1.0))

    def test_transparent(self):
        self.assertEqual(contrast.parse_color("transparent")[3], 0.0)

    def test_rejects_nonsense(self):
        with self.assertRaises(contrast.ColorError):
            contrast.parse_color("not-a-color")

    def test_rejects_empty(self):
        with self.assertRaises(contrast.ColorError):
            contrast.parse_color("")


class TestContrastRatio(unittest.TestCase):
    def test_black_on_white_is_twenty_one(self):
        ratio = contrast.contrast_ratio("#000000", "#ffffff")
        self.assertAlmostEqual(ratio, 21.0, places=6)

    def test_identical_colors_are_one(self):
        ratio = contrast.contrast_ratio("#336699", "#336699")
        self.assertAlmostEqual(ratio, 1.0, places=6)

    def test_symmetric(self):
        forward = contrast.contrast_ratio("#777777", "#ffffff")
        backward = contrast.contrast_ratio("#ffffff", "#777777")
        self.assertAlmostEqual(forward, backward, places=9)

    def test_known_wcag_value(self):
        # #767676 on white is the canonical 4.54:1 AA boundary.
        ratio = contrast.contrast_ratio("#767676", "#ffffff")
        self.assertAlmostEqual(ratio, 4.54, places=2)

    def test_large_text_boundary(self):
        # #949494 on white is the canonical 3.0:1 value.
        ratio = contrast.contrast_ratio("#949494", "#ffffff")
        self.assertAlmostEqual(ratio, 3.0, places=1)

    def test_translucent_foreground_is_composited(self):
        opaque = contrast.contrast_ratio("#808080", "#ffffff")
        translucent = contrast.contrast_ratio("rgba(0, 0, 0, 0.5)", "#ffffff")
        # Half-alpha black over white sits near mid grey, so
        # the two ratios land in the same neighbourhood.
        self.assertGreater(translucent, 1.0)
        self.assertLess(abs(translucent - opaque), 2.0)


class TestVerdicts(unittest.TestCase):
    def test_failing_ratio_fails_aa_text(self):
        result = contrast.verdicts(1.2)
        self.assertFalse(result["AA normal text (1.4.3)"])
        self.assertFalse(result["AA non-text / UI boundary (1.4.11)"])

    def test_border_ratio_of_three_passes_non_text_only(self):
        result = contrast.verdicts(3.0)
        self.assertTrue(result["AA non-text / UI boundary (1.4.11)"])
        self.assertFalse(result["AA normal text (1.4.3)"])

    def test_high_ratio_passes_everything(self):
        result = contrast.verdicts(17.6)
        for label in result:
            self.assertTrue(result[label], label)


CSS = """
/* a comment { with braces } to confuse a naive parser */
:root {
  --bg: #ffffff;
  --surface: #fbfbfb;
  --ink: #111111;
  --muted: #5f6b7a;
  --line: #f0f0f0;
  --measure: 38rem;
  --radius: 8px;
  --accent: var(--ink);
}
body {
  color: var(--ink);
}
[data-theme="dark"] {
  --bg: #101418;
  --ink: #e8eaed;
  --line: #232a31;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101418;
  }
}
"""


class TestExtractBlocks(unittest.TestCase):
    def test_finds_each_block_that_declares_properties(self):
        blocks = contrast.extract_blocks(CSS)
        selectors = [block["selector"] for block in blocks]
        self.assertEqual(selectors.count(":root"), 2)
        self.assertIn('[data-theme="dark"]', selectors)

    def test_blocks_without_custom_properties_are_dropped(self):
        blocks = contrast.extract_blocks(CSS)
        self.assertNotIn("body", [block["selector"] for block in blocks])

    def test_media_context_is_recorded(self):
        blocks = contrast.extract_blocks(CSS)
        nested = [block for block in blocks if block["at"]]
        self.assertEqual(len(nested), 1)
        self.assertIn("prefers-color-scheme", nested[0]["at"][0])

    def test_comments_do_not_open_a_block(self):
        blocks = contrast.extract_blocks(CSS)
        self.assertEqual(blocks[0]["selector"], ":root")


class TestCustomProperties(unittest.TestCase):
    def test_base_block_is_extracted(self):
        properties = contrast.extract_custom_properties(CSS)
        self.assertIn("ink", properties)
        self.assertIn("measure", properties)
        self.assertEqual(properties["ink"], "#111111")

    def test_theme_block_does_not_leak_into_the_base(self):
        properties = contrast.extract_custom_properties(CSS)
        self.assertEqual(properties["bg"], "#ffffff")

    def test_scope_layers_the_theme_over_the_base(self):
        properties = contrast.extract_custom_properties(CSS, scope="dark")
        self.assertEqual(properties["bg"], "#101418")
        self.assertEqual(properties["ink"], "#e8eaed")
        # Unthemed values still come through from the base.
        self.assertEqual(properties["surface"], "#fbfbfb")

    def test_non_colour_properties_are_dropped(self):
        colors = contrast.color_properties(CSS)
        self.assertNotIn("measure", colors)
        self.assertNotIn("radius", colors)

    def test_colour_properties_are_kept(self):
        colors = contrast.color_properties(CSS)
        self.assertEqual(colors["ink"], "#111111")
        self.assertEqual(colors["muted"], "#5f6b7a")

    def test_var_reference_is_resolved(self):
        colors = contrast.color_properties(CSS)
        self.assertEqual(colors["accent"], "#111111")

    def test_the_low_contrast_border_is_found(self):
        # A common finding: a border the eye accepts and the
        # arithmetic rejects. 1.4.11 asks for 3:1.
        colors = contrast.color_properties(CSS)
        ratio = contrast.contrast_ratio(colors["line"], colors["surface"])
        self.assertLess(ratio, 3.0)

    def test_the_border_also_misses_in_the_dark_theme(self):
        colors = contrast.color_properties(CSS, scope="dark")
        ratio = contrast.contrast_ratio(colors["line"], colors["bg"])
        self.assertLess(ratio, 3.0)

    def test_body_text_passes_aa_in_both_themes(self):
        light = contrast.color_properties(CSS)
        dark = contrast.color_properties(CSS, scope="dark")
        self.assertGreater(contrast.contrast_ratio(light["ink"], light["bg"]), 4.5)
        self.assertGreater(contrast.contrast_ratio(dark["ink"], dark["bg"]), 4.5)


class TestCli(unittest.TestCase):
    def test_ratio_subcommand_runs(self):
        self.assertEqual(contrast.main(["ratio", "#000", "#fff"]), 0)

    def test_bad_colour_exits_nonzero(self):
        self.assertEqual(contrast.main(["ratio", "nope", "#fff"]), 1)

    def test_no_subcommand_prints_help(self):
        self.assertEqual(contrast.main([]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
