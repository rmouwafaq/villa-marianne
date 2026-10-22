import re

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
            if not path.endswith("/slug") and path not in ("/lang", "/site", "/nav/saly", "/nav/contact", "/beach_fmt", "/whatsapp",
                        "/form/countries/FR", "/pages/legal/sections[3]/h"):  # noms propres identiques
                self.assertTrue(str(value).strip(), path)
                self.assertNotEqual(value, fr[path], path)


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestEnglishPages(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")

    def test_english_and_french_home(self):
        fr = self.url_open("/").text
        self.assertIn("à vendre", fr)
        en = self.url_open("/en/").text
        self.assertIn("Villa Marianne", en)
        self.assertIn("for sale", en)

    def test_language_switcher_links(self):
        fr = self.url_open("/la-villa").text
        self.assertRegex(fr, r'class="hbm-switch" href="//[^"/]+/en/la-villa"')
        en = self.url_open("/en/la-villa").text
        self.assertRegex(en, r'class="hbm-switch" href="//[^"/]+/fr/la-villa"')

    def test_switch_link_uses_request_host_not_base_url(self):
        """web.base.url peut être faux (ex. localhost:8069) : le lien doit suivre l'adresse réellement utilisée."""
        self.env["ir.config_parameter"].sudo().set_param("web.base.url", "http://wrong.example:1234")
        for path in ("/la-villa", "/en/la-villa"):
            html = self.url_open(path).text
            self.assertNotIn("wrong.example", re.search(r'class="hbm-switch" href="([^"]+)"', html).group(1))
            self.assertRegex(html, r'class="hbm-switch" href="//127\.0\.0\.1:8069/')

    def test_french_is_default_whatever_the_browser_language(self):
        self.opener.cookies.clear()
        for accept in ("en-US,en;q=0.9", "en-GB", "nl-BE", "ar-MA", "fr-FR"):
            res = self.url_open("/la-villa", headers={"Accept-Language": accept}, allow_redirects=False)
            self.assertEqual(res.status_code, 200, accept)
            self.assertIn("Galerie photos", res.text, accept)

    def test_back_to_french_sticks_after_english(self):
        self.opener.cookies.clear()
        self.opener.cookies.set("frontend_lang", "en_US", domain="127.0.0.1", path="/")
        res = self.url_open("/fr/la-villa")  # lien « Français » : suit la redirection
        self.assertIn("Galerie photos", res.text)
        self.assertEqual(self.opener.cookies.get("frontend_lang", domain="127.0.0.1", path="/"), "fr_FR")
        again = self.url_open("/la-villa", allow_redirects=False)
        self.assertEqual(again.status_code, 200)
        self.assertIn("Galerie photos", again.text)

    def test_website_configurator_is_marked_done(self):
        website = self.env["website"].search([], limit=1)
        self.assertTrue(website.configurator_done)
        todo = self.env.ref("website.website_configurator_todo")
        self.assertEqual(todo.state, "done")