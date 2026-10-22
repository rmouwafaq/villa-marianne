import json
import re

from odoo.tests.common import HttpCase, TransactionCase, tagged

from ..content import PAGE_PATHS


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestJsonLd(TransactionCase):

    def test_json_ld_listing(self):
        data = self.env["hbm.property"].get_main().json_ld("fr")
        self.assertEqual(data["@type"], "RealEstateListing")
        self.assertEqual(data["offers"]["price"], 280000)
        self.assertEqual(data["offers"]["priceCurrency"], "EUR")
        address = data["contentLocation"]["address"]
        self.assertEqual(address["addressLocality"], "Saly")
        self.assertEqual(address["addressCountry"], "SN")

    def test_json_ld_price_follows_property(self):
        prop = self.env["hbm.property"].get_main()
        prop.price = 295000
        self.assertEqual(prop.json_ld("en")["offers"]["price"], 295000)


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestSeoHead(HttpCase):

    def _pages(self):
        for key, path in PAGE_PATHS.items():
            yield "fr", key, path
            yield "en", key, "/en" + ("" if path == "/" else path)

    def test_head_tags_every_page(self):
        self.opener.cookies.set("frontend_lang", "fr_FR")
        for lang, key, path in self._pages():
            html = self.url_open(path).text
            self.assertEqual(html.count('rel="canonical"'), 1, path)
            self.assertIn('hreflang="x-default"', html, path)
            self.assertIn('hreflang="en"', html, path)
            match = re.search(r'<meta name="description" content="([^"]*)"', html)
            self.assertTrue(match, path)
            self.assertTrue(70 <= len(match.group(1)) <= 160, (path, len(match.group(1))))
            self.assertIn('property="og:title"', html, path)
            self.assertIn('property="og:image"', html, path)

    def test_json_ld_in_page_is_valid(self):
        self.opener.cookies.set("frontend_lang", "fr_FR")
        html = self.url_open("/la-villa").text
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertTrue(blocks)
        graph = json.loads(blocks[0])["@graph"]
        types = {item["@type"] for item in graph}
        self.assertIn("RealEstateListing", types)
        self.assertIn("Organization", types)

    def test_buy_page_has_faq(self):
        self.opener.cookies.set("frontend_lang", "fr_FR")
        html = self.url_open("/acheter-au-senegal").text
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        types = {item["@type"] for b in blocks for item in json.loads(b)["@graph"]}
        self.assertIn("FAQPage", types)


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestSitemap(HttpCase):

    def test_sitemap_lists_both_languages(self):
        body = self.url_open("/sitemap.xml").text
        if "<sitemapindex" in body:  # plusieurs fichiers : on les concatène
            for url in re.findall(r"<loc>([^<]+)</loc>", body):
                body += self.url_open("/" + url.split("/", 3)[3]).text
        self.assertRegex(body, r"<loc>[^<]*/la-villa</loc>")
        self.assertRegex(body, r"<loc>[^<]*/en/la-villa</loc>")
        self.assertNotIn("/en/en/", body)

    def test_sitemap_urls_all_resolve(self):
        """Aucune URL du sitemap ni aucun hreflang ne doit mener à une erreur."""
        body = self.url_open("/sitemap.xml").text
        locs = re.findall(r"<loc>([^<]+)</loc>", body)
        self.assertGreaterEqual(len(locs), 24)
        for loc in locs:
            path = "/" + loc.split("/", 3)[3]
            res = self.url_open(path)
            self.assertEqual(res.status_code, 200, path)
            for href in re.findall(r'<link rel="alternate" hreflang="[^"]+" href="([^"]+)"', res.text):
                alt = "/" + href.split("/", 3)[3]
                self.assertEqual(self.url_open(alt).status_code, 200, alt)

    def test_robots_points_to_sitemap(self):
        self.assertIn("Sitemap:", self.url_open("/robots.txt").text)
