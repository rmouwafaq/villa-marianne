from odoo import http

from . import controllers
from . import models


def _default_lang_french(self):
    """Le français est la langue par défaut de ce site, quelle que soit la langue du navigateur.

    Odoo prend sinon la langue du navigateur pour toute nouvelle session et redirige les
    navigateurs anglophones vers /en/. L'anglais reste accessible par /en/ (lien « English »).
    Ce réglage vaut pour toute l'instance Odoo, qui est dédiée à ce site.
    """
    return "fr_FR"


http.Request.default_lang = _default_lang_french
