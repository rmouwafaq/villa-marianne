import re

from odoo.tests.common import HttpCase, tagged

from ..controllers import lead as lead_controller

NBSP = " "


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestBrochure(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")
        lead_controller.RATE_HITS.clear()

    def _request_brochure(self, kind="brochure", email="doc@example.com"):
        page = self.url_open("/contact").text
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        self.url_open("/hbm/lead", data={
            "csrf_token": token, "name": "Doc Test", "email": email, "country": "FR",
            "profile": "investor", "request": kind, "lang": "fr", "fmt": "json"})
        return self.env["crm.lead"].search([("email_from", "=", email)])

    def test_brochure_pdf_with_token(self):
        lead = self._request_brochure()
        self.assertTrue(lead.hbm_brochure_token)
        mail = self.env["mail.mail"].search([("email_to", "ilike", "doc@example.com")])
        self.assertIn(f"/hbm/brochure/{lead.hbm_brochure_token}", mail.body_html)
        # 1re génération après un changement de code : wkhtmltopdf recompile les assets du rapport (> 12 s)
        res = self.url_open(f"/hbm/brochure/{lead.hbm_brochure_token}", timeout=90)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))
        self.assertEqual(self.url_open("/hbm/brochure/inconnu").status_code, 404)

    def test_visit_request_gets_no_brochure_link(self):
        lead = self._request_brochure(kind="visit_video", email="visit@example.com")
        mail = self.env["mail.mail"].search([("email_to", "ilike", "visit@example.com")])
        self.assertNotIn("/hbm/brochure/", mail.body_html)
        self.assertTrue(lead)

    def test_brochure_reflects_price(self):
        prop = self.env["hbm.property"].get_main()
        prop.price = 295000
        report = self.env["ir.actions.report"]
        html, _ = report._render_qweb_html(
            "hbm_villa_sale.report_brochure", [prop.id], data={"lang": "fr"})
        self.assertIn("295" + NBSP + "000", html.decode())
        self.assertNotIn("250" + NBSP + "000", html.decode())

    def test_brochure_embeds_photos(self):
        """Photos en base64 : wkhtmltopdf ne doit dépendre d'aucune URL réseau."""
        prop = self.env["hbm.property"].get_main()
        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            "hbm_villa_sale.report_brochure", [prop.id], data={"lang": "fr"})
        html = html.decode()
        self.assertEqual(html.count("data:image/jpeg;base64,"), 8)
        self.assertNotIn("/hbm_villa_sale/static/img/brochure", html)

    def test_brochure_english(self):
        prop = self.env["hbm.property"].get_main()
        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            "hbm_villa_sale.report_brochure", [prop.id], data={"lang": "en"})
        self.assertIn("Villa for sale", html.decode())
