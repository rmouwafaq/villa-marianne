import time
from datetime import timedelta

from odoo import fields, http
from odoo.http import request
from odoo.tools import plaintext2html
from odoo.tools.mail import email_normalize

PROFILES = ("investor", "second_home", "diaspora")
REQUESTS = ("brochure", "visit_onsite", "visit_video")
RATE_MAX, RATE_WINDOW = 5, 60  # demandes par adresse IP et par minute
RATE_HITS = {}  # ip -> horodatages (par processus : suffisant contre un envoi en rafale)


def _rate_limited(ip, now):
    hits = [t for t in RATE_HITS.get(ip, []) if now - t < RATE_WINDOW]
    limited = len(hits) >= RATE_MAX
    if not limited:
        hits.append(now)
    RATE_HITS[ip] = hits
    return limited


def _utm(model, name):
    if not name:
        return False
    env = request.env[model].sudo()
    return (env.search([("name", "=", name)], limit=1) or env.create({"name": name})).id


class HbmLead(http.Controller):

    def _answer(self, post, ok, error=None):
        if post.get("fmt") == "json":
            return request.make_json_response({"ok": True} if ok else {"ok": False, "error": error})
        return request.redirect("/contact?status=" + ("ok" if ok else error), code=303)

    @http.route("/hbm/lead", type="http", auth="public", website=True, methods=["POST"])
    def submit(self, **post):
        if post.get("company_site"):  # champ piège : un robot l'a rempli, rejet silencieux
            return self._answer(post, True)
        if _rate_limited(request.httprequest.remote_addr, time.time()):
            return self._answer(post, False, "rate")
        name = (post.get("name") or "").strip()
        email = email_normalize((post.get("email") or "").strip())
        if not name or not email:
            return self._answer(post, False, "error")

        Lead = request.env["crm.lead"].sudo()
        recent = fields.Datetime.now() - timedelta(seconds=RATE_WINDOW)
        if Lead.search_count([("email_from", "=", email), ("hbm_web", "=", True),
                              ("create_date", ">=", recent)]):
            return self._answer(post, True)  # double envoi : une seule opportunité

        country = request.env["res.country"].sudo().search(
            [("code", "=", (post.get("country") or "").upper())], limit=1)
        tags = []
        if country:
            Tag = request.env["crm.tag"].sudo()
            tag = Tag.search([("name", "=", country.code)], limit=1) or Tag.create({"name": country.code})
            tags = [(4, tag.id)]
        profile = post.get("profile")
        request_kind = post.get("request")
        lang = post.get("lang") if post.get("lang") in ("fr", "en") else "fr"
        details = "\n".join(filter(None, [post.get("message"), post.get("budget")]))
        lead = Lead.create({
            "name": f"Villa Marianne - {name}",
            "type": "opportunity",
            "contact_name": name,
            "email_from": email,
            "phone": (post.get("phone") or "").strip(),
            "description": plaintext2html(details) if details else False,
            "country_id": country.id,
            "tag_ids": tags,
            "hbm_web": True,
            "hbm_profile": profile if profile in PROFILES else False,
            "hbm_request": request_kind if request_kind in REQUESTS else "brochure",
            "hbm_budget": post.get("budget") or False,
            "hbm_lang": lang,
            "source_id": _utm("utm.source", post.get("utm_source")),
            "campaign_id": _utm("utm.campaign", post.get("utm_campaign")),
            "medium_id": _utm("utm.medium", post.get("utm_medium")),
        })
        lead._hbm_send("confirm")
        lead._hbm_notify_seller()
        return self._answer(post, True)
