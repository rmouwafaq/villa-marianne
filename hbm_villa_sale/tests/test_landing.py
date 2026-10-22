import re

from markupsafe import escape

from odoo.tests.common import HttpCase, tagged

from ..content import CONTENT

LANDINGS = {"fr": "/investir-saly", "en": "/saly-villa-for-sale"}


def _main(html):
    return html.split('<main id="hbm-main"')[1].split("</main>")[0]


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestLanding(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")

    def test_landing_single_cta_no_menu(self):
        for lang, path in LANDINGS.items():
            html = self.url_open(path).text
            main = _main(html)
            self.assertIn('action="/hbm/lead"', main, path)
            self.assertEqual(main.count('class="hbm-btn'), 1, path)
            self.assertNotIn('class="hbm-nav"', html, path)
            self.assertIn(CONTENT[lang]["pages"]["landing"]["lead"], main, path)

    def test_landing_never_redirects_on_browser_language(self):
        """Une page d'atterrissage Ads reste à son adresse, quelle que soit la langue du navigateur."""
        for lang, path in LANDINGS.items():
            for accept in ("en-US,en;q=0.9", "fr-FR,fr;q=0.9", "ar-MA"):
                res = self.url_open(path, headers={"Accept-Language": accept}, allow_redirects=False)
                self.assertEqual(res.status_code, 200, (path, accept))
                self.assertIn(CONTENT[lang]["pages"]["landing"]["lead"], res.text, (path, accept))
                self.assertIn(f'rel="canonical" href="http://127.0.0.1:8069{path}"', res.text)

    def test_landing_is_noindex(self):
        for path in LANDINGS.values():
            self.assertRegex(self.url_open(path).text,
                             r'<meta name="robots" content="noindex', path)

    def test_landing_form_returns_to_landing(self):
        path = LANDINGS["fr"]
        html = self.url_open(path).text
        token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
        res = self.url_open("/hbm/lead", data={
            "csrf_token": token, "name": "Land Test", "email": "land@example.com",
            "country": "FR", "profile": "investor", "request": "brochure",
            "lang": "fr", "next": path}, allow_redirects=False)
        self.assertIn(path + "?status=ok", res.headers["Location"])

    def test_next_parameter_cannot_redirect_elsewhere(self):
        html = self.url_open("/contact").text
        token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
        res = self.url_open("/hbm/lead", data={
            "csrf_token": token, "name": "Evil", "email": "evil@example.com",
            "country": "FR", "lang": "fr", "next": "https://evil.example/"},
            allow_redirects=False)
        self.assertNotIn("evil.example", res.headers["Location"])


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestArticles(HttpCase):

    def setUp(self):
        super().setUp()
        self.opener.cookies.set("frontend_lang", "fr_FR")

    def test_blog_index_lists_articles(self):
        html = self.url_open("/conseils").text
        for article in CONTENT["fr"]["articles"]:
            self.assertIn(f'/conseils/{article["slug"]}', html)

    def test_each_article_seo_and_link_to_villa(self):
        self.assertGreaterEqual(len(CONTENT["fr"]["articles"]), 4)
        for lang, prefix in (("fr", ""), ("en", "/en")):
            for article in CONTENT[lang]["articles"]:
                html = self.url_open(f'{prefix}/conseils/{article["slug"]}').text
                self.assertIn(f"<h1>{escape(article['title'])}</h1>", html, article["slug"])
                meta = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
                self.assertTrue(70 <= len(meta) <= 160, (article["slug"], len(meta)))
                self.assertIn('href="/la-villa"', _main(html).replace('href="/en/la-villa"', 'href="/la-villa"'))

    def test_unknown_article_is_404(self):
        self.assertEqual(self.url_open("/conseils/inconnu").status_code, 404)

    def test_sitemap_has_articles(self):
        body = self.url_open("/sitemap.xml").text
        for article in CONTENT["fr"]["articles"]:
            self.assertRegex(body, rf"<loc>[^<]*/conseils/{article['slug']}</loc>")
            self.assertRegex(body, rf"<loc>[^<]*/en/conseils/{article['slug']}</loc>")

    def test_articles_have_no_yield_promises(self):
        for lang in ("fr", "en"):
            for article in CONTENT[lang]["articles"]:
                text = " ".join(article["body"])
                self.assertNotRegex(text, r"\d\s?%", article["slug"])
