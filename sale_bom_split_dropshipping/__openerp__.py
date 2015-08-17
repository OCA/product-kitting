# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{'name': 'Sales BoMs Split - Dropshipping (compatibility)',
 'version': '1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Sales & Purchases',
 'depends': ['sale_bom_split',
             # https://github.com/OCA/sale-workflow/tree/7.0
             'sale_dropshipping',
             ],
 'description': """
Sales BoMs Split - Dropshipping (compatibility)
===============================================

Compatibility module between **Sales BoM Split** and
**Sale Dropshipping**.

When a line with a Bill of Material in a sales order has
a drop shipping setup, the procurements generated for the
components will also be in drop shipping.

 """,
 'website': 'http://www.camptocamp.com',
 'data': [],
 'test': [],
 'installable': True,
 'auto_install': True,
 }
