# -*- coding: utf-8 -*-
######################################################################
#
#  Note: Program metadata is available in /__init__.py
#
######################################################################

{
    "name" : "Sellable Product Quantity",
    "version" : "1.8.1",
    "author" : 'Ursa Information Systems',
    "summary": "Generate and display that can be sold (Ursa)",
    "description" : """
This module creates a new field on a product called Quantity You Can Sell and the associated logic to calculate and display this in the UI.


OpenERP Version:  8.0
Ursa Dev Team: RC

Contact: contact@ursainfosystems.com
""",
    'maintainer': 'Ursa Information Systems',
    'website': 'http://www.ursainfosystems.com',
    "category": 'Accounting & Finance',
    "images" : [],
    "depends" : ["base",'sale_stock','warning'],
    "data" : [ "product_view.xml","sale_view.xml"],
    "test" : [
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

