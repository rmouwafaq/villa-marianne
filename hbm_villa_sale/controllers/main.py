import json

from markupsafe import Markup

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import Website

from ..content import CONTENT, PAGE_PATHS


def _hbm_sitemap(env, rule, qs):
    """Toutes les pages du module, dans les deux langues (Odoo ne liste que la langue par défaut)."""
    for path in PAGE_PATHS.values():
        for loc in (path, "/en" + ("" if path == "/" else path)):
            if not qs or qs.lower() in loc:
                yield {"loc": loc}


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
        page_url = request.httprequest.base_url
        og_image = host + "/hbm_villa_sale/static/img/og-default.jpg"
        graph = prop.seo_graph(lang, key, url=page_url, image=og_image, base_url=host)
        # "<" échappé : le JSON est inséré tel quel dans un bloc <script>
        ld_json = Markup(json.dumps(graph, ensure_ascii=False).replace("<", "\\u003c"))
        return request.render("hbm_villa_sale.page", {
            "ld_json": ld_json,
            "hbm_seo": {"title": c["pages"][key]["title"], "og_image": og_image,
                        "locale": "fr_FR" if lang == "fr" else "en_US", "url": page_url},
            "key": key,
            "c": c,
            "page": c["pages"][key],
            "paths": PAGE_PATHS,
            "prop": prop,
            "facts": prop.public_facts(c),
            "alt_path": alt_path,
        })

    @http.route(sitemap=_hbm_sitemap)
    def index(self, **kw):
        return self._hbm_render("home")

    @http.route("/la-villa", type="http", auth="public", website=True, sitemap=False)
    def villa(self, **kw):
        return self._hbm_render("villa")

    @http.route("/investir", type="http", auth="public", website=True, sitemap=False)
    def invest(self, **kw):
        return self._hbm_render("invest")

    @http.route("/saly", type="http", auth="public", website=True, sitemap=False)
    def saly(self, **kw):
        return self._hbm_render("saly")

    @http.route("/acheter-au-senegal", type="http", auth="public", website=True, sitemap=False)
    def buy(self, **kw):
        return self._hbm_render("buy")

    @http.route("/contact", type="http", auth="public", website=True, sitemap=False)
    def contact(self, **kw):
        return self._hbm_render("contact")

    @http.route("/mentions-legales", type="http", auth="public", website=True, sitemap=False)
    def legal(self, **kw):
        return self._hbm_render("legal")
