from odoo import api, fields, models

from ..content import CONTENT

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

    @staticmethod
    def format_number(value):
        return f"{value:,.0f}".replace(",", " ")

    def price_display(self):
        self.ensure_one()
        symbol = self.currency_id.symbol or self.currency_id.name
        return f"{self.format_number(self.price)} {symbol}"

    def price_equivalents(self):
        """Équivalents indicatifs (MAD, CHF) ; vide tant que les taux ne sont pas saisis."""
        self.ensure_one()
        out = []
        for code in ("MAD", "CHF"):
            value = self.price_in(code)
            if value:
                out.append(f"≈\u00a0{self.format_number(value)}\u00a0{code}")
        return out

    def public_facts(self, c):
        """Liste (clé, libellé, valeur) pour la page, dans la langue du catalogue `c`."""
        self.ensure_one()
        fmt = self.format_number
        labels = c["fact_labels"]
        area = f"{fmt(self.area_m2)} m² ({c['area_labels'][self.area_label]})"
        suites = c["suites_fmt"].format(min=self.suites_min, max=self.suites_max)
        values = [
            ("price", self.price_display()),
            ("area", area),
            ("year", str(self.year_built)),
            ("beach", c["beach_fmt"].format(n=self.distance_beach_m)),
            ("suites", suites),
            ("legal", self.legal_status or c["on_request"]),
        ]
        return [(key, labels[key], value) for key, value in values]

    def json_ld(self, lang, url=None, image=None):
        """Données structurées schema.org de l'annonce (RealEstateListing + Offer + Place)."""
        self.ensure_one()
        home = CONTENT[lang]["pages"]["home"]
        data = {
            "@context": "https://schema.org",
            "@type": "RealEstateListing",
            "name": home["title"].split(" | ")[0],
            "description": home["meta"],
            "inLanguage": lang,
            "offers": {
                "@type": "Offer",
                "price": self.price,
                "priceCurrency": self.currency_id.name,
                "availability": "https://schema.org/InStock",
            },
            "contentLocation": {
                "@type": "Place",
                "name": "Saly",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Saly",
                    "addressCountry": "SN",
                },
            },
        }
        if url:
            data["url"] = url
        if image:
            data["image"] = image
        return data

    def seo_graph(self, lang, key, url=None, image=None, base_url=None):
        """Liste JSON-LD d'une page : organisation, annonce (accueil/villa), FAQ (achat)."""
        self.ensure_one()
        c = CONTENT[lang]
        organization = {"@type": "Organization", "name": c["site"]}
        if base_url:
            organization["url"] = base_url
        graph = [organization]
        if key in ("home", "villa"):
            listing = self.json_ld(lang, url=url, image=image)
            listing.pop("@context")
            graph.append(listing)
        faq = c["pages"][key].get("faq")
        if faq:
            graph.append({
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": item["q"],
                     "acceptedAnswer": {"@type": "Answer", "text": item["a"]}}
                    for item in faq
                ],
            })
        return {"@context": "https://schema.org", "@graph": graph}

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
