from odoo.tests.common import HttpCase, TransactionCase, tagged

from ..content import CONTENT


def _leaf_paths(node, prefix=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _leaf_paths(value, f"{prefix}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _leaf_paths(value, f"{prefix}[{index}]")
    else:
        yield prefix, node


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestCatalogParity(TransactionCase):

    def test_fr_en_same_structure_and_non_empty(self):
        fr = dict(_leaf_paths(CONTENT["fr"]))
        en = dict(_leaf_paths(CONTENT["en"]))
        self.assertEqual(sorted(fr), sorted(en))
        for path, value in en.items():
            if path != "/lang":
                self.assertTrue(str(value).strip(), path)
                self.assertNotEqual(value, fr[path], path)


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestEnglishPages(HttpCase):

    def test_english_and_french_home(self):
        fr = self.url_open("/", headers={"Cookie": "frontend_lang=fr_FR"}).text
        self.assertIn("à vendre", fr)
        en = self.url_open("/en/").text
        self.assertIn("Villa Marianne", en)
        self.assertIn("for sale", en)

    def test_language_switcher_links(self):
        fr = self.url_open("/la-villa", headers={"Cookie": "frontend_lang=fr_FR"}).text
        self.assertIn('href="/en/la-villa"', fr)
        en = self.url_open("/en/la-villa").text
        self.assertIn('href="/la-villa"', en)
