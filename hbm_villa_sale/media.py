"""Chargement du manifeste des photos (data/media_manifest.json), partagé site et brochure."""
import json

from odoo.tools import file_path

_MANIFEST = []


def manifest():
    if not _MANIFEST:
        with open(file_path("hbm_villa_sale/data/media_manifest.json"), encoding="utf-8") as handle:
            _MANIFEST.extend(json.load(handle))
    return _MANIFEST
