import json

from markupsafe import Markup

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import Website

from ..content import CONTENT, PAGE_PATHS
from ..media import manifest

IMG_URL = "/hbm_villa_sale/static/img/"
SPACE_ORDER = ["exterior", "pool", "aerial", "terraces", "interior", "night", "environment"]
LANDING_LANG = {"/investir-saly": "fr", "/saly-villa-for-sale": "en"}


def _hbm_sitemap(env, rule, qs):
    """Pages et articles du module, dans les deux langues (Odoo ne liste que la langue par défaut)."""
    paths = list(PAGE_PATHS.values())
    paths += [f"/conseils/{article['slug']}" for article in CONTENT["fr"]["articles"]]
    for path in paths:
        for loc in (path, "/en" + ("" if path == "/" else path)):
            if not qs or qs.lower() in loc:
                yield {"loc": loc}


def _image_attrs(item, lang):
    """Attributs <img> responsive d'une entrée du manifeste."""
    widths = item["widths"]
    shown = max((w for w in widths if w <= 1280), default=widths[0])
    return {
        "name": item["name"],
        "space": item["space"],
        "src": f"{IMG_URL}{item['name']}-{shown}.webp",
        "srcset": ", ".join(f"{IMG_URL}{item['name']}-{w}.webp {w}w" for w in widths),
        "width": shown,
        "height": round(shown * item["ratio"]),
        "alt": item["alt_" + lang],
        "hero": item["hero"],
    }


def _gallery(lang):
    return sorted((_image_attrs(m, lang) for m in manifest()),
                  key=lambda i: SPACE_ORDER.index(i["space"]))


class HbmVillaSale(Website):

    def _hbm_render(self, key, lang=None, article=None):
        """Rend une page du catalogue. `key` : home, villa, ... blog, article, landing."""
        # UTM conservés dans la session serveur (pas de cookie supplémentaire avant consentement)
        for utm in ("utm_source", "utm_medium", "utm_campaign"):
            if request.params.get(utm):
                request.session["hbm_" + utm] = request.params[utm][:100]
        landing = key == "landing"
        lang = lang or ("en" if (request.env.lang or "").startswith("en") else "fr")
        c = CONTENT[lang]
        if article:
            page = {"title": f"{article['title']} | {c['site']}", "meta": article["meta"],
                    "lead": article["lead"],
                    "sections": [{"h": "", "p": article["body"], "ul": []}]}
        else:
            page = c["pages"][key]
        prop = request.env["hbm.property"].sudo().get_main()
        params = request.env["ir.config_parameter"].sudo()
        path = request.httprequest.path
        # URL absolues : Odoo re-préfixe les liens relatifs avec la langue courante.
        host = request.website.get_base_url().rstrip("/")
        # selon la version, Odoo peut ou non retirer le préfixe de langue du chemin
        if path == "/en" or path.startswith("/en/"):
            path = path[3:] or "/"
        fr_url = host + path
        en_url = host + "/en" + ("" if path == "/" else path)
        # Lien de changement de langue : adresse réellement utilisée par le visiteur (web.base.url peut
        # être faux), sans schéma pour qu'Odoo ne le re-préfixe pas. « /fr/ » mémorise le choix du français.
        switch_host = "//" + request.httprequest.host
        alt_path = switch_host + ("/fr" if lang == "en" else "/en") + ("" if path == "/" else path)
        page_url = host + path if landing else (en_url if lang == "en" else fr_url)
        og_image = host + "/hbm_villa_sale/static/img/og-default.jpg"
        graph = prop.seo_graph(lang, "blog" if article else key, url=page_url,
                               image=og_image, base_url=host)
        # "<" échappé : le JSON est inséré tel quel dans un bloc <script>
        ld_json = Markup(json.dumps(graph, ensure_ascii=False).replace("<", "\\u003c"))
        status = request.params.get("status")
        digits = "".join(ch for ch in (params.get_param("hbm_villa_sale.whatsapp") or "") if ch.isdigit())
        gallery = _gallery(lang) if key in ("home", "villa", "landing") else []
        return request.render("hbm_villa_sale.page", {
            "key": key,
            "c": c,
            "page": page,
            "article": article,
            "landing": landing,
            "paths": PAGE_PATHS,
            "prop": prop,
            "facts": prop.public_facts(c),
            "alt_path": alt_path,
            "canonical": page_url,
            "alternates": None if landing else {"fr": fr_url, "en": en_url},
            "next_path": path if landing else "/contact",
            "gallery": gallery if key == "villa" else [],
            "hero": next((i for i in gallery if i["hero"]), None) if key in ("home", "landing") else None,
            "ld_json": ld_json,
            "equivalents": prop.price_equivalents() if key in ("home", "landing") else [],
            "status": status if status in c["form"]["status"] else None,
            "whatsapp_url": f"https://wa.me/{digits}" if digits else None,
            "gtm_id": params.get_param("hbm_villa_sale.gtm_id") or None,
            "hbm_seo": {"title": page["title"], "og_image": og_image, "noindex": landing,
                        "locale": "fr_FR" if lang == "fr" else "en_US", "url": page_url},
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

    @http.route("/conseils", type="http", auth="public", website=True, sitemap=False)
    def blog(self, **kw):
        return self._hbm_render("blog")

    @http.route("/conseils/<string:slug>", type="http", auth="public", website=True, sitemap=False)
    def article(self, slug, **kw):
        lang = "en" if (request.env.lang or "").startswith("en") else "fr"
        article = next((a for a in CONTENT[lang]["articles"] if a["slug"] == slug), None)
        if not article:
            raise request.not_found()
        return self._hbm_render("article", article=article)

    # Pages d'atterrissage Google Ads : une langue par adresse, hors sitemap, non indexées.
    # multilang=False : Odoo ne redirige pas vers /en/ selon la langue du navigateur.
    @http.route("/investir-saly", type="http", auth="public", website=True, multilang=False, sitemap=False)
    def landing_fr(self, **kw):
        return self._hbm_render("landing", lang="fr")

    @http.route("/saly-villa-for-sale", type="http", auth="public", website=True, multilang=False, sitemap=False)
    def landing_en(self, **kw):
        return self._hbm_render("landing", lang="en")
