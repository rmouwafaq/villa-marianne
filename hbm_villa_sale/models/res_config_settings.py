from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hbm_rate_mad = fields.Float(
        string="Taux EUR → MAD", config_parameter="hbm_villa_sale.rate_mad")
    hbm_rate_chf = fields.Float(
        string="Taux EUR → CHF", config_parameter="hbm_villa_sale.rate_chf")
    hbm_seller_email = fields.Char(
        string="E-mail du vendeur", config_parameter="hbm_villa_sale.seller_email")
    hbm_whatsapp = fields.Char(
        string="WhatsApp (format international)",
        config_parameter="hbm_villa_sale.whatsapp")
