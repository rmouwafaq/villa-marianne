import re
import shutil
import subprocess
import unittest

from odoo.tests.common import HttpCase, TransactionCase, tagged
from odoo.tools import file_path

from ..controllers import lead as lead_controller


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestTrackingJs(TransactionCase):

    def test_node_unit_tests(self):
        if not shutil.which("node"):
            raise unittest.SkipTest("node absent")
        tests_dir = file_path("hbm_villa_sale/static/tests")
        result = subprocess.run(["node", "--test", tests_dir], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestTracking(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")
        lead_controller.RATE_HITS.clear()
        self.params = self.env["ir.config_parameter"].sudo()

    def test_no_gtm_script_in_html_even_with_id(self):
        self.params.set_param("hbm_villa_sale.gtm_id", "GTM-TEST")
        html = self.url_open("/").text
        self.assertIn('id="hbm-consent"', html)
        self.assertIn('data-gtm-id="GTM-TEST"', html)
        self.assertNotIn("googletagmanager.com", html)

    def test_consent_can_be_withdrawn(self):
        self.params.set_param("hbm_villa_sale.gtm_id", "GTM-TEST")
        self.assertIn("data-hbm-consent-reset", self.url_open("/").text)
        self.params.set_param("hbm_villa_sale.gtm_id", "")
        self.assertNotIn("data-hbm-consent-reset", self.url_open("/").text)

    def test_no_banner_without_gtm_id(self):
        self.params.set_param("hbm_villa_sale.gtm_id", "")
        self.assertNotIn('id="hbm-consent"', self.url_open("/").text)

    def test_banner_hidden_until_js_decides(self):
        self.params.set_param("hbm_villa_sale.gtm_id", "GTM-TEST")
        html = self.url_open("/").text
        self.assertRegex(html, r'id="hbm-consent"[^>]*\shidden')

    def test_confirmation_marker(self):
        self.assertIn('data-status="ok"', self.url_open("/contact?status=ok").text)
        self.assertNotIn('data-status="ok"', self.url_open("/contact").text)

    def test_utm_persist_to_lead(self):
        self.url_open("/?utm_source=google&utm_campaign=fr-invest&utm_medium=cpc")
        page = self.url_open("/contact").text
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        self.url_open("/hbm/lead", data={
            "csrf_token": token, "name": "Utm Test", "email": "utm@example.com",
            "country": "FR", "profile": "investor", "request": "brochure",
            "lang": "fr", "fmt": "json"})
        lead = self.env["crm.lead"].search([("email_from", "=", "utm@example.com")])
        self.assertEqual(lead.source_id.name, "google")
        self.assertEqual(lead.campaign_id.name, "fr-invest")
        self.assertEqual(lead.medium_id.name, "cpc")
