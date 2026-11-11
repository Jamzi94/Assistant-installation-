from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from stremio_publication import (  # noqa: E402
    PAL_SOURCE,
    apply_stremio_overrides,
    validate_stremio_overrides,
)


class StremioPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))

    def test_current_data_satisfies_verified_contract(self):
        self.assertEqual(len(validate_stremio_overrides(self.document)), 5)

    def test_source_link_is_only_in_pal_step_five(self):
        app = self.document["apps"]["stremio"]
        for device in ("iphone", "ipad"):
            steps = next(m["steps"] for m in app["install"][device] if m["id"] == "pal")
            occurrences = [
                (index + 1, link[1])
                for index, step in enumerate(steps)
                for link in step.get("links", [])
                if len(link) == 2 and link[1] == PAL_SOURCE
            ]
            self.assertEqual(occurrences, [(5, PAL_SOURCE)])

    def test_altstore_pal_open_instruction_occurs_once_at_step_five(self):
        app = self.document["apps"]["stremio"]
        for device in ("iphone", "ipad"):
            steps = next(m["steps"] for m in app["install"][device] if m["id"] == "pal")
            step5 = steps[4]
            text = " ".join([step5.get("title", ""), step5.get("body", ""), *step5.get("substeps", [])]).lower()
            self.assertEqual(text.count("ouvre altstore pal"), 1)
            for index, step in enumerate(steps):
                if index != 4:
                    other = (step.get("title", "") + " " + step.get("body", "")).lower()
                    self.assertNotIn("ouvre altstore pal", other)

    def test_region_and_illustration_corrections(self):
        app = self.document["apps"]["stremio"]
        phone = next(m["steps"] for m in app["install"]["iphone"] if m["id"] == "pal")
        tablet = next(m["steps"] for m in app["install"]["ipad"] if m["id"] == "pal")
        self.assertIn("Brésil", phone[0]["body"])
        self.assertIn("physiquement dans l’Union européenne", tablet[0]["body"])
        self.assertIn("pas son app PAL pour iPad au Japon ni au Brésil", tablet[0]["body"])
        self.assertNotIn("image", tablet[0])
        self.assertEqual(phone[1]["image"], "assets/methods/stremio/pal-download.svg")
        self.assertEqual(tablet[1]["image"], "assets/methods/stremio/pal-download.svg")
        self.assertTrue(phone[1]["image_alt"].startswith("Illustration : page altstore.io"))
        self.assertTrue((ROOT / phone[1]["image"]).is_file())

    def test_classic_is_separate_and_conditional(self):
        app = self.document["apps"]["stremio"]
        for device in ("iphone", "ipad"):
            classic = next(m for m in app["install"][device] if m["id"] == "classic_info")
            self.assertIn("IPA", classic["label"])
            self.assertTrue(any("Windows" in link[0] for link in classic["steps"][1].get("links", [])))
            self.assertTrue(any("macOS" in link[0] for link in classic["steps"][1].get("links", [])))
            self.assertFalse(any(link[1] == PAL_SOURCE for step in classic["steps"] for link in step.get("links", [])))

    def test_overrides_are_idempotent(self):
        document = copy.deepcopy(self.document)
        apply_stremio_overrides(document)
        once = copy.deepcopy(document)
        apply_stremio_overrides(document)
        self.assertEqual(document, once)

    def test_old_shared_pal_links_are_migrated_and_new_links_versioned(self):
        js = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
        self.assertIn("const legacyPalLink", js)
        self.assertIn("rawStep >= 4", js)
        self.assertIn("(query.get('tab') || 'overview') === 'install'", js)
        self.assertIn("query.set('gv', '2')", js)
        self.assertIn("last.step = Number(last.step) + 1", js)
        self.assertIn("guideVersion: state.app === 'stremio'", js)


if __name__ == "__main__":
    unittest.main()
