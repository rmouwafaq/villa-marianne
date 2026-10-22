import uuid
from datetime import timedelta

from odoo import fields, models

# (étape actuelle, jours depuis la demande, étape suivante, type de message)
FOLLOWUPS = ((0, 3, 1, "followup1"), (1, 10, 2, "followup2"))


class CrmLead(models.Model):
    _inherit = "crm.lead"

    hbm_web = fields.Boolean(string="Demande du site Villa Marianne", copy=False)
    hbm_profile = fields.Selection(
        [("investor", "Investissement"), ("second_home", "Résidence secondaire"),
         ("diaspora", "Projet familial ou retour au pays")], string="Profil")
    hbm_request = fields.Selection(
        [("brochure", "Dossier complet"), ("visit_onsite", "Visite sur place"),
         ("visit_video", "Visite en visio")], string="Demande")
    hbm_budget = fields.Char(string="Budget envisagé")
    hbm_lang = fields.Selection([("fr", "Français"), ("en", "English")], default="fr")
    hbm_followup_stage = fields.Integer(string="Relances envoyées", default=0, copy=False)

    hbm_brochure_token = fields.Char(default=lambda self: uuid.uuid4().hex, copy=False, index=True)

    def hbm_brochure_url(self):
        self.ensure_one()
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base}/hbm/brochure/{self.hbm_brochure_token}"

    def _hbm_send(self, kind):
        """Met en file l'e-mail `kind` (confirm, followup1, followup2) dans la langue de la demande."""
        for lead in self:
            template = self.env.ref(f"hbm_villa_sale.mail_{kind}_{lead.hbm_lang or 'fr'}")
            template.send_mail(lead.id, force_send=False)

    def _hbm_notify_seller(self):
        seller = self.env["ir.config_parameter"].sudo().get_param("hbm_villa_sale.seller_email")
        if not seller:
            return
        for lead in self:
            self.env["mail.mail"].sudo().create({
                "subject": f"Villa Marianne : nouvelle demande de {lead.contact_name}",
                "email_to": seller,
                "body_html": (
                    f"<p>{lead.contact_name} ({lead.email_from}) a envoyé une demande "
                    f"({lead.hbm_request}, projet : {lead.hbm_profile}).</p>"),
                "auto_delete": True,
            })

    def _cron_hbm_followups(self):
        """Relances à J+3 et J+10 tant que la demande reste à la première étape du pipeline."""
        first_stage = self.env["crm.stage"].search([], order="sequence, id", limit=1)
        now = fields.Datetime.now()
        leads = self.search([
            ("hbm_web", "=", True), ("hbm_followup_stage", "<", 2),
            ("stage_id", "=", first_stage.id),
        ])
        for lead in leads:
            for current, days, following, kind in FOLLOWUPS:
                if lead.hbm_followup_stage == current and lead.create_date <= now - timedelta(days=days):
                    lead._hbm_send(kind)
                    lead.hbm_followup_stage = following
                    break
