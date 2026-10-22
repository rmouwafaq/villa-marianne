from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestProperty(TransactionCase):

    def test_main_property_defaults(self):
        prop = self.env["hbm.property"].get_main()
        self.assertEqual(prop.price, 280000)
        self.assertEqual(prop.currency_id.name, "EUR")
        self.assertEqual(prop.year_built, 2006)
        self.assertEqual(prop.distance_beach_m, 400)
        self.assertEqual(prop.area_label, "unknown")

    def test_price_in_uses_settings_rates(self):
        prop = self.env["hbm.property"].get_main()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("hbm_villa_sale.rate_mad", "0")
        self.assertIsNone(prop.price_in("MAD"))
        params.set_param("hbm_villa_sale.rate_mad", "10.8")
        self.assertEqual(prop.price_in("MAD"), 3024000.0)
        self.assertEqual(prop.price_in("EUR"), 280000)
