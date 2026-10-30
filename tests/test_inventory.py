"""Tests for the pass-one page inventory.

Every test here is offline. `probe()` is the only function
that touches the network and it is not exercised.
"""

import os
import sys
import unittest

SKILL_SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "skill",
    "scripts",
)
sys.path.insert(0, SKILL_SCRIPTS)

import inventory  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    with open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as handle:
        return handle.read()


class TestAttributes(unittest.TestCase):
    def test_double_quoted(self):
        self.assertEqual(
            inventory.attributes('lang="en" dir="ltr"'), {"lang": "en", "dir": "ltr"}
        )

    def test_single_quoted(self):
        self.assertEqual(inventory.attributes("lang='en'"), {"lang": "en"})

    def test_unquoted(self):
        self.assertEqual(inventory.attributes("lang=en"), {"lang": "en"})

    def test_names_are_lowercased(self):
        self.assertEqual(inventory.attributes('LANG="en"'), {"lang": "en"})


class TestVisibleText(unittest.TestCase):
    def test_drops_script_bodies(self):
        text = inventory.visible_text("<p>keep</p><script>var drop = 1;</script>")
        self.assertIn("keep", text)
        self.assertNotIn("drop", text)

    def test_drops_style_bodies(self):
        text = inventory.visible_text("<style>.a{color:red}</style><p>keep</p>")
        self.assertNotIn("color", text)


class TestGoodPage(unittest.TestCase):
    def setUp(self):
        self.report = inventory.analyze_html(fixture("good.html"))

    def test_lang_is_found(self):
        self.assertTrue(self.report["has_lang"])
        self.assertEqual(self.report["lang"], "en")

    def test_title_is_decoded(self):
        self.assertEqual(self.report["title"], "A perfectly ordinary page")

    def test_social_metadata_is_detected(self):
        self.assertTrue(self.report["has_social_metadata"])
        self.assertIn("og:title", self.report["open_graph"])
        self.assertIn("twitter:card", self.report["twitter_card"])

    def test_viewport_is_detected(self):
        self.assertTrue(self.report["has_viewport"])

    def test_icon_link_is_detected(self):
        self.assertTrue(self.report["has_icon_link"])

    def test_no_entity_leak(self):
        self.assertFalse(self.report["has_entity_leak"])
        self.assertEqual(self.report["raw_entities_in_title"], [])

    def test_alt_text_present(self):
        self.assertEqual(self.report["img_count"], 1)
        self.assertEqual(self.report["img_missing_alt"], 0)

    def test_headings_counted(self):
        self.assertEqual(self.report["headings"]["h1"], 1)


class TestBadPage(unittest.TestCase):
    """The fixture reproduces representative pass-one findings."""

    def setUp(self):
        self.report = inventory.analyze_html(fixture("bad.html"))

    def test_missing_lang_is_flagged(self):
        self.assertFalse(self.report["has_lang"])
        self.assertIsNone(self.report["lang"])

    def test_double_escaped_entity_leaks_into_the_title(self):
        self.assertIn("&#8211;", self.report["raw_entities_in_title"])

    def test_entity_leaks_into_visible_text(self):
        self.assertTrue(self.report["has_entity_leak"])
        self.assertIn("&#8211;", self.report["raw_entities_in_text"])

    def test_no_social_metadata(self):
        self.assertFalse(self.report["has_social_metadata"])
        self.assertEqual(self.report["open_graph"], [])

    def test_no_viewport(self):
        self.assertFalse(self.report["has_viewport"])

    def test_no_icon_link(self):
        self.assertFalse(self.report["has_icon_link"])

    def test_missing_alt_is_counted(self):
        self.assertEqual(self.report["img_count"], 2)
        self.assertEqual(self.report["img_missing_alt"], 1)

    def test_media_elements_are_counted(self):
        self.assertEqual(self.report["audio_count"], 3)

    def test_inline_script_is_measured(self):
        self.assertGreater(self.report["inline_script_bytes"], 0)

    def test_interactive_elements_are_counted(self):
        self.assertEqual(self.report["input_count"], 1)
        self.assertEqual(self.report["link_count"], 2)


class TestRobots(unittest.TestCase):
    def test_comments_only_is_flagged(self):
        text = "# a preamble\n# more preamble\n\n"
        report = inventory.analyze_robots(text)
        self.assertEqual(report["directive_count"], 0)
        self.assertTrue(report["comments_only"])

    def test_directives_are_collected(self):
        text = "# note\nUser-agent: *\nDisallow: /private/\n"
        report = inventory.analyze_robots(text)
        self.assertEqual(report["directive_count"], 2)
        self.assertFalse(report["comments_only"])

    def test_empty_file_is_not_comments_only(self):
        report = inventory.analyze_robots("")
        self.assertFalse(report["comments_only"])


class TestExtraUrls(unittest.TestCase):
    def test_derives_the_four_probes_from_the_origin(self):
        urls = inventory.extra_urls("https://example.com/deep/page/?q=1")
        self.assertEqual(urls[0], "https://example.com/robots.txt")
        self.assertEqual(urls[1], "https://example.com/sitemap.xml")
        self.assertEqual(urls[2], "https://example.com/favicon.ico")
        self.assertTrue(urls[3].startswith("https://example.com/"))
        self.assertNotEqual(urls[3], "https://example.com/")


class TestRender(unittest.TestCase):
    def test_zero_byte_404_is_called_out(self):
        record = {
            "url": "https://example.com/nobody-here/",
            "status": 404,
            "bytes": 0,
            "elapsed_ms": 12,
            "content_type": "text/plain",
            "rate_limit_headers": {"ratelimit-limit": "10"},
        }
        output = inventory.render_text([record])
        self.assertIn("zero-byte body", output)
        self.assertIn("ratelimit-limit: 10", output)

    def test_missing_lang_is_called_out(self):
        record = {
            "url": "https://example.com/",
            "status": 200,
            "bytes": 100,
            "elapsed_ms": 5,
            "content_type": "text/html",
            "rate_limit_headers": {},
            "html": inventory.analyze_html(fixture("bad.html")),
        }
        output = inventory.render_text([record])
        self.assertIn("no lang attribute", output)
        self.assertIn("no Open Graph", output)

    def test_error_record_renders(self):
        record = {"url": "https://example.invalid/", "error": "URLError: no host"}
        output = inventory.render_text([record])
        self.assertIn("ERROR", output)


if __name__ == "__main__":
    unittest.main(verbosity=1)
