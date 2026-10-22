import base64

from odoo import api, models
from odoo.tools import file_path

from ..content import CONTENT
from ..media import manifest

BROCHURE_PHOTOS = ["courtyard-palm", "villa-facade-garden", "pool-garden-view", "pool-wide",
                   "aerial-complex", "dining-room", "living-room", "terrace-table-pool"]


def _data_uri(name):
    with open(file_path(f"hbm_villa_sale/static/img/brochure/{name}.jpg"), "rb") as handle:
        return "data:image/jpeg;base64," + base64.b64encode(handle.read()).decode()


class ReportBrochure(models.AbstractModel):
    _name = "report.hbm_villa_sale.report_brochure"
    _description = "Brochure Villa Marianne"

    @api.model
    def _get_report_values(self, docids, data=None):
        lang = (data or {}).get("lang")
        lang = lang if lang in CONTENT else "fr"
        c = CONTENT[lang]
        docs = self.env["hbm.property"].browse(docids)
        by_name = {m["name"]: m for m in manifest()}
        params = self.env["ir.config_parameter"].sudo()
        return {
            "doc_ids": docids,
            "doc_model": "hbm.property",
            "docs": docs,
            "c": c,
            "title": c["pages"]["home"]["title"].split(" | ")[0],
            "facts": docs[:1].public_facts(c),
            "equivalents": docs[:1].price_equivalents(),
            "photos": [{"src": _data_uri(name), "alt": by_name[name]["alt_" + lang]}
                       for name in BROCHURE_PHOTOS],
            "seller_email": params.get_param("hbm_villa_sale.seller_email"),
            "whatsapp": params.get_param("hbm_villa_sale.whatsapp"),
        }
