# -*- coding: utf-8 -*-
# © 2015 Camptocamp SA, Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Compute Stock from BoM",
    "summary": "Compute Product Stock from its Bill of Material",
    "version": "8.0.1.0.0",
    "category": "Manufacturing",
    "website": "https://odoo-community.org/",
    "author": "Camptocamp SA, Sodexis, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        'delivery',
        'mrp',
        'stock_available_immediately',
    ],
    "data": [
        "views/product_template_view.xml",
        "views/res_company_view.xml"
    ],
    "test": [
        'tests/test_bom_stock.yml',
    ],
    'images': [
        'images/bom_stock.png'
    ],
}
