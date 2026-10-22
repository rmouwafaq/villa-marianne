from odoo import api, fields, models

RATE_PARAMS = {"MAD": "hbm_villa_sale.rate_mad", "CHF": "hbm_villa_sale.rate_chf"}


class HbmProperty(models.Model):
    _name = "hbm.property"
    _description = "Bien immobilier à vendre"

    name = fields.Char(required=True, translate=True)
    currency_id = fields.Many2one(
        "res.currency", required=True,
        default=lambda self: self.env.ref("base.EUR"))
    price = fields.Monetary(currency_field="currency_id")
    area_m2 = fields.Float(string="Surface (m²)")
    area_label = fields.Selection(
        [("land", "Terrain"), ("built", "Bâti"), ("unknown", "À confirmer")],
        default="unknown", required=True)
    legal_status = fields.Char(translate=True)
    year_built = fields.Integer()
    distance_beach_m = fields.Integer()
    suites_min = fields.Integer()
    suites_max = fields.Integer()
    description = fields.Html(translate=True, sanitize_attributes=False)

    @api.model
    def get_main(self):
        return self.search([], order="id", limit=1)

    def price_in(self, currency_code):
        """Prix converti, ou None si le taux n'est pas renseigné."""
        self.ensure_one()
        if currency_code == self.currency_id.name:
            return self.price
        param = RATE_PARAMS.get(currency_code)
        if not param:
            return None
        rate = float(self.env["ir.config_parameter"].sudo().get_param(param) or 0)
        return round(self.price * rate, 2) if rate else None
