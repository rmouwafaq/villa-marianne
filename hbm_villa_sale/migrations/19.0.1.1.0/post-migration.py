"""Prix de vente ramené de 280 000 € à 250 000 € (négociable).

Les données du bien sont chargées une seule fois (noupdate) : une simple mise à jour du module
ne changerait pas le prix d'une base existante. Un prix déjà modifié à la main n'est pas touché.
"""


def migrate(cr, version):
    cr.execute("UPDATE hbm_property SET price = 250000 WHERE price = 280000")
