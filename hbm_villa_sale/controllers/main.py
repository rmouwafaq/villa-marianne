from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import Website

from ..content import CONTENT, PAGE_PATHS


class HbmVillaSale(Website):

    def _hbm_render(self, key):
        lang = "en" if (request.env.lang or "").startswith("en") else "fr"
        c = CONTENT[lang]
        prop = request.env["hbm.property"].sudo().get_main()
        path = request.httprequest.path
        # URL absolue : Odoo re-préfixe les liens relatifs avec la langue courante.
        host = request.httprequest.host_url.rstrip("/")
        if lang == "en":
            # selon la version, Odoo peut ou non retirer le préfixe du chemin
            if path.startswith("/en"):
                path = path[3:] or "/"
            alt_path = host + path
        else:
            alt_path = host + "/en" + (path if path != "/" else "/")
        return request.render("hbm_villa_sale.page", {
            "key": key,
            "c": c,
            "page": c["pages"][key],
            "paths": PAGE_PATHS,
            "prop": prop,
            "facts": prop.public_facts(c),
            "alt_path": alt_path,
        })

    @http.route()
    def index(self, **kw):
        return self._hbm_render("home")

    @http.route("/la-villa", type="http", auth="public", website=True, sitemap=True)
    def villa(self, **kw):
        return self._hbm_render("villa")

    @http.route("/investir", type="http", auth="public", website=True, sitemap=True)
    def invest(self, **kw):
        return self._hbm_render("invest")

    @http.route("/saly", type="http", auth="public", website=True, sitemap=True)
    def saly(self, **kw):
        return self._hbm_render("saly")

    @http.route("/acheter-au-senegal", type="http", auth="public", website=True, sitemap=True)
    def buy(self, **kw):
        return self._hbm_render("buy")

    @http.route("/contact", type="http", auth="public", website=True, sitemap=True)
    def contact(self, **kw):
        return self._hbm_render("contact")

    @http.route("/mentions-legales", type="http", auth="public", website=True, sitemap=True)
    def legal(self, **kw):
        return self._hbm_render("legal")
