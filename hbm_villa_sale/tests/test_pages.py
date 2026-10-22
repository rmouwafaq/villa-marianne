from odoo.tests.common import HttpCase, tagged

ROUTES = [
    "/", "/la-villa", "/investir", "/saly", "/acheter-au-senegal",
    "/contact", "/mentions-legales",
]
NBSP = " "


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestPages(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")

    def test_public_pages_ok(self):
        for route in ROUTES:
            res = self.url_open(route)
            self.assertEqual(res.status_code, 200, route)
        home = self.url_open("/").text
        self.assertIn("280" + NBSP + "000", home)
        invest = self.url_open("/investir").text
        main = invest.split('<main id="hbm-main"')[1].split("</main>")[0]
        self.assertNotIn("%", main)
        self.assertNotIn("rentabilité de", main)

    def test_price_change_propagates(self):
        self.env["hbm.property"].get_main().price = 295000
        home = self.url_open("/").text
        self.assertIn("295" + NBSP + "000", home)
        self.assertNotIn("280" + NBSP + "000", home)

    def test_price_equivalents_follow_settings(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("hbm_villa_sale.rate_mad", "0")
        params.set_param("hbm_villa_sale.rate_chf", "0")
        self.assertNotIn("MAD", self.url_open("/").text)
        params.set_param("hbm_villa_sale.rate_mad", "10.8")
        params.set_param("hbm_villa_sale.rate_chf", "0.93")
        home = self.url_open("/").text
        self.assertIn("3" + NBSP + "024" + NBSP + "000" + NBSP + "MAD", home)
        self.assertIn("260" + NBSP + "400" + NBSP + "CHF", home)
        self.assertIn("indicatifs", home)
        self.assertIn("Indicative equivalents", self.url_open("/en/").text)

    def test_legal_page_has_retention_and_cookies(self):
        fr = self.url_open("/mentions-legales").text
        self.assertIn("conservées", fr)
        self.assertIn("cookies", fr)
        en = self.url_open("/en/mentions-legales").text
        self.assertIn("retained", en)
        self.assertIn("cookies", en)

    def test_empty_legal_status_shows_on_request(self):
        self.env["hbm.property"].get_main().legal_status = False
        villa = self.url_open("/la-villa").text
        self.assertIn("sur demande", villa)
        self.assertNotIn("False", villa)
