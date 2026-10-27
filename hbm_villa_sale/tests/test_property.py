import importlib.util

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install", "hbm_villa_sale")
class TestProperty(TransactionCase):

    def test_main_property_defaults(self):
        prop = self.env["hbm.property"].get_main()
        self.assertEqual(prop.price, 250000)
        self.assertTrue(prop.price_negotiable)
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
        self.assertEqual(prop.price_in("MAD"), 2700000.0)
        self.assertEqual(prop.price_in("EUR"), 250000)

    def _migrate(self):
        spec = importlib.util.spec_from_file_location(
            "post_migration", file_path("hbm_villa_sale/migrations/19.0.1.1.0/post-migration.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "19.0.1.0.0")

    def test_migration_lowers_old_default_price(self):
        prop = self.env["hbm.property"].get_main()
        prop.price = 280000
        prop.flush_recordset()
        self._migrate()
        prop.invalidate_recordset()
        self.assertEqual(prop.price, 250000)

    def test_migration_keeps_a_price_changed_by_hand(self):
        prop = self.env["hbm.property"].get_main()
        prop.price = 262000
        prop.flush_recordset()
        self._migrate()
        prop.invalidate_recordset()
        self.assertEqual(prop.price, 262000)
