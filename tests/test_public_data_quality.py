from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicDataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
        cls.serialized = json.dumps(cls.document, ensure_ascii=False)

    def test_public_json_has_no_known_dead_or_malformed_links(self):
        forbidden = (
            "support.google.com/androidtv",
            "how-to-sideload-apps-on-the-fire-tv",
            "googletv/?hl=franswer/",
            "apps.apple.com/no/app/kdtivi-unify-iptv-vod",
            "apps.apple.com/fr/search?term=KDTIVI",
        )
        for value in forbidden:
            self.assertNotIn(value, self.serialized)

    def test_android_and_fire_tv_help_use_verified_landing_pages(self):
        self.assertIn("https://support.google.com/googletv/?hl=fr", self.serialized)
        self.assertIn("https://www.aftvnews.com/downloader/", self.serialized)

    def test_public_copy_does_not_reference_the_source_bot(self):
        for term in ("chatbot", "telegram", "whatsapp", "bot"):
            self.assertNotIn(term, self.serialized.lower())

    def test_kdtivi_apple_installation_uses_publisher_landing_page(self):
        app = self.document["apps"]["kdtivi"]
        self.assertEqual(app["site"], "https://kdtapps.com/kdtivi")
        self.assertEqual(app["source"], "https://kdtapps.com/kdtivi")
        for device in ("apple_tv", "iphone", "ipad"):
            self.assertEqual(app["links"][device], "https://kdtapps.com/kdtivi")

    def test_generated_timestamp_and_schema_are_present(self):
        self.assertEqual(self.document["schema_version"], 1)
        self.assertRegex(self.document["generated_at"], r"^20\d\d-\d\d-\d\dT")

    def test_static_html_has_basic_security_headers(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="Content-Security-Policy"', html)
        self.assertIn('name="referrer" content="no-referrer"', html)


if __name__ == "__main__":
    unittest.main()
