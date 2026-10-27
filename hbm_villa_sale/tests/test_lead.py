import json
import re
from datetime import timedelta

from odoo import fields
from odoo.tests.common import HttpCase, tagged

from ..controllers import lead as lead_controller


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestLead(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")
        lead_controller.RATE_HITS.clear()
        self.Lead = self.env["crm.lead"]

    def _post(self, **extra):
        """Envoie le formulaire comme un navigateur : jeton CSRF lu sur la page contact."""
        page = self.url_open("/contact").text
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        data = {"csrf_token": token, "name": "Claire Martin", "email": "claire@example.com",
                "country": "FR", "profile": "investor", "request": "brochure",
                "lang": "fr", "fmt": "json"}
        data.update(extra)
        return self.url_open("/hbm/lead", data=data, allow_redirects=False)

    def _leads(self, email="claire@example.com"):
        return self.Lead.search([("email_from", "=", email)])

    def test_lead_created(self):
        res = self._post(utm_source="google")
        self.assertEqual(res.json(), {"ok": True})
        lead = self._leads()
        self.assertEqual(len(lead), 1)
        self.assertEqual(lead.country_id.code, "FR")
        self.assertIn("FR", lead.tag_ids.mapped("name"))
        self.assertEqual(lead.hbm_profile, "investor")
        self.assertEqual(lead.hbm_request, "brochure")
        self.assertEqual(lead.source_id.name, "google")
        self.assertTrue(lead.hbm_web)

    def test_invalid_email_rejected(self):
        res = self._post(email="pas-un-email")
        self.assertFalse(res.json()["ok"])
        self.assertFalse(self.Lead.search([("contact_name", "=", "Claire Martin")]))

    def test_double_submit_single_lead(self):
        self._post()
        self._post()
        self.assertEqual(len(self._leads()), 1)

    def test_honeypot_and_rate_limit(self):
        res = self._post(company_site="http://spam.example")
        self.assertTrue(res.json()["ok"])  # rejet silencieux
        self.assertFalse(self._leads())
        for i in range(5):
            self.assertTrue(self._post(email=f"v{i}@example.com").json()["ok"])
        sixth = self._post(email="v6@example.com").json()
        self.assertFalse(sixth["ok"])
        self.assertEqual(sixth["error"], "rate")
        self.assertFalse(self._leads("v6@example.com"))

    def test_confirmation_language(self):
        self._post(email="en@example.com", lang="en")
        self._post(email="fr@example.com", lang="fr")
        Mail = self.env["mail.mail"]
        en = Mail.search([("email_to", "ilike", "en@example.com")])
        fr = Mail.search([("email_to", "ilike", "fr@example.com")])
        self.assertIn("received your request", en.subject)
        self.assertIn("bien reçu votre demande", fr.subject)

    def test_seller_notified(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "hbm_villa_sale.seller_email", "vendeur@example.com")
        self._post()
        mails = self.env["mail.mail"].search([("email_to", "=", "vendeur@example.com")])
        self.assertEqual(len(mails), 1)

    def test_seller_notification_escapes_visitor_input(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "hbm_villa_sale.seller_email", "vendeur@example.com")
        self._post(name='<a href="https://evil.example">Cliquez</a>\nBcc: x@example.com',
                   email="xss@example.com")
        mail = self.env["mail.mail"].search([("email_to", "=", "vendeur@example.com")])
        self.assertEqual(len(mail), 1)
        self.assertNotIn('<a href="https://evil.example">', mail.body_html)
        self.assertIn("&lt;a href=", mail.body_html)
        self.assertNotIn("\n", mail.subject)
        self.assertIn("Investissement", mail.body_html)  # libellé, pas la clé « investor »
        self.assertNotIn("investor", mail.body_html)

    def test_form_works_without_js(self):
        page = self.url_open("/contact").text
        token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
        res = self.url_open("/hbm/lead", data={
            "csrf_token": token, "name": "Paul", "email": "paul@example.com",
            "country": "BE", "profile": "second_home", "request": "visit_video", "lang": "fr"},
            allow_redirects=False)
        self.assertIn(res.status_code, (302, 303))
        self.assertIn("/contact?status=ok", res.headers["Location"])
        self.assertEqual(len(self._leads("paul@example.com")), 1)

    def test_followups_sent_and_stopped(self):
        self._post(email="a@example.com")
        self._post(email="b@example.com")
        lead_a, lead_b = self._leads("a@example.com"), self._leads("b@example.com")
        # b est qualifiée : passée dans une étape suivante
        stages = self.env["crm.stage"].search([], order="sequence, id")
        lead_b.stage_id = stages[1]
        old = fields.Datetime.now() - timedelta(days=4)
        self.env.cr.execute("UPDATE crm_lead SET create_date=%s WHERE id IN %s",
                            (old, (lead_a.id, lead_b.id)))
        self.env.invalidate_all()
        # seuls les e-mails de ces deux demandes comptent : la base peut contenir d'autres demandes
        Mail = self.env["mail.mail"]
        mine = [("email_to", "in", ["a@example.com", "b@example.com"])]
        before = Mail.search_count(mine)
        self.Lead._cron_hbm_followups()
        self.assertEqual(Mail.search_count(mine) - before, 1)
        self.assertEqual(lead_a.hbm_followup_stage, 1)
        self.assertEqual(lead_b.hbm_followup_stage, 0)
        # J+10 : une seule relance de plus pour a, aucune si on relance tout de suite
        self.Lead._cron_hbm_followups()
        self.assertEqual(lead_a.hbm_followup_stage, 1)
        old = fields.Datetime.now() - timedelta(days=11)
        self.env.cr.execute("UPDATE crm_lead SET create_date=%s WHERE id=%s", (old, lead_a.id))
        self.env.invalidate_all()
        self.Lead._cron_hbm_followups()
        self.assertEqual(lead_a.hbm_followup_stage, 2)
        self.Lead._cron_hbm_followups()
        self.assertEqual(lead_a.hbm_followup_stage, 2)

    def test_contact_page_has_form_and_honeypot(self):
        page = self.url_open("/contact").text
        self.assertIn('action="/hbm/lead"', page)
        self.assertIn('name="company_site"', page)
        self.assertIn(json.dumps("csrf_token")[1:-1], page)
