import json
import os

from odoo.tests.common import HttpCase, tagged
from odoo.tools import file_path

IMG_DIR = os.path.join("hbm_villa_sale", "static", "img")


def _manifest():
    with open(file_path("hbm_villa_sale/data/media_manifest.json"), encoding="utf-8") as handle:
        return json.load(handle)


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestMedia(HttpCase):

    def test_manifest_complete(self):
        manifest = _manifest()
        self.assertGreaterEqual(len(manifest), 30)
        self.assertEqual(len({m["name"] for m in manifest}), len(manifest))
        for item in manifest:
            self.assertTrue(item["alt_fr"].strip(), item["name"])
            self.assertTrue(item["alt_en"].strip(), item["name"])
            for width in item["widths"]:
                path = file_path(f"{IMG_DIR}/{item['name']}-{width}.webp")
                self.assertTrue(os.path.exists(path), path)

    def test_gallery_renders_all(self):
        self.opener.cookies.set("frontend_lang", "fr_FR")
        manifest = _manifest()
        html = self.url_open("/la-villa").text
        main = html.split('<main id="hbm-main"')[1].split("</main>")[0]
        self.assertEqual(main.count('class="hbm-gallery-img"'), len(manifest))
        self.assertEqual(main.count('loading="lazy"'), len(manifest) - 1)
        self.assertIn(manifest[0]["alt_fr"], main)

    def test_gallery_alt_in_english(self):
        manifest = _manifest()
        html = self.url_open("/en/la-villa").text
        self.assertIn(manifest[0]["alt_en"], html)

    def test_home_has_hero_image(self):
        html = self.url_open("/").text
        self.assertIn('class="hbm-hero-img"', html)
