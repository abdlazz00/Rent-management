{
    "name": "Rental Management",
    "category": "rent",
    "license": "AGPL-3",
    "author": "Abdul Aziz",
    "version": "1.0",
    "website": " ",
    "summary": "Rental Management",
    "depends": ["base", "mail", "web"],
    "data": [
        "data/document_type_data.xml",
        "data/sequence.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/vehicle_views.xml",
        "views/vehicle_brand_views.xml",
        "views/booking_transaction_views.xml",
        "views/booking_payment_views.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "rent_management/static/src/css/vehicle_kanban.css",
        ],
    },
    "installable": True,
    "application": True,
}
