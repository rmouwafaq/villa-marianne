{
    "name": "Villa Marianne - Vente",
    "version": "19.0.1.0.0",
    "summary": "Site web de vente de la Villa Marianne (Saly, Sénégal)",
    "category": "Website",
    "license": "LGPL-3",
    "depends": ["website", "crm", "website_crm", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/property_data.xml",
        "views/property_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "application": True,
    "installable": True,
}
