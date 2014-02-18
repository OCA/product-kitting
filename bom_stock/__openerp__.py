# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Compute Stock from BoM',
    'version': '5.0.1',
    'category': 'Generic Modules/Others',
    'description':
     """Compute the BOM  stock Value. BoM Stock Value are computed by:
      (`Reference stock` of `Product` + How much could I produce of that `Product` according to the component's `Reference Stock`)

      This reference stock can be chosen by company through a selection field
      and can be one of the available stock quantity computed in the system :
      Available stock, Virtual stock, immediately_usable stock (from
      stock_available_immediately)."""
    ,
    'author': 'Camptocamp',
    'website': 'http://www.camptocamp.com',
    'depends': ['stock',
                'mrp',
                'stock_available_immediately',
                ],
    'data': ['bom_stock_view.xml'],
    'demo': [],
    'test': ['tests/test_bom_stock.yml',
             ],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
