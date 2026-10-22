from odoo import http
from odoo.http import request


class HbmBrochure(http.Controller):

    @http.route("/hbm/brochure/<string:token>", type="http", auth="public", website=True,
                multilang=False, sitemap=False)
    def brochure(self, token, **kw):
        lead = request.env["crm.lead"].sudo().search([("hbm_brochure_token", "=", token)], limit=1)
        if not lead:
            raise request.not_found()
        prop = request.env["hbm.property"].sudo().get_main()
        report = request.env["ir.actions.report"].sudo().with_context(force_report_rendering=True)
        pdf, _ = report._render_qweb_pdf(
            "hbm_villa_sale.report_brochure", [prop.id], data={"lang": lead.hbm_lang or "fr"})
        return request.make_response(pdf, headers=[
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", 'inline; filename="villa-marianne.pdf"'),
        ])
