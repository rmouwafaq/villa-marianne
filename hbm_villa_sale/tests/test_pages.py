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

    def test_empty_legal_status_shows_on_request(self):
        self.env["hbm.property"].get_main().legal_status = False
        villa = self.url_open("/la-villa").text
        self.assertIn("sur demande", villa)
        self.assertNotIn("False", villa)
