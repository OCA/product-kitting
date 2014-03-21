# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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

from openerp.osv.orm import Model
from openerp.addons.mrp.mrp import rounding


class mrp_bom(Model):

    _inherit = 'mrp.bom'

    def _bom_split_vals(self, cr, uid, bom, factor, context=None):
        product_obj = self.pool['product.product']
        return {
            'name': product_obj.name_get(cr, uid, [bom.product_id.id])[0][1],
            'product_id': bom.product_id.id,
            'product_qty': bom.product_qty * factor,
            'product_uom': bom.product_uom.id,
            'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
            'product_uos': bom.product_uos and bom.product_uos.id or False,
        }

    def bom_split(self, cr, uid, bom, factor, addthis=False, level=0):
        """
        split the bom into components.
        factor is the quantity to produce  expressed in bom product_uom
        """
        factor = factor / (bom.product_efficiency or 1.0)
        factor = rounding(factor, bom.product_rounding)
        if factor < bom.product_rounding:
            factor = bom.product_rounding
        result = []
        phantom = False
        if bom.type == 'phantom' and not bom.bom_lines:
            newbom = self._bom_find(
                cr, uid, bom.product_id.id, bom.product_uom.id)

            if newbom:
                result += self.bom_split(
                    cr, uid, self.browse(cr, uid, [newbom])[0],
                    factor * bom.product_qty,
                    addthis=True,
                    level=level+10)
                phantom = True
            else:
                phantom = False

        if bom.type == 'normal' and bom.bom_lines:
            result.append(self._bom_split_vals(cr, uid, bom, factor))

        elif not phantom:
            if addthis and not bom.bom_lines:
                result.append(self._bom_split_vals(cr, uid, bom, factor))

            for bom2 in bom.bom_lines:
                result += self.bom_split(
                    cr, uid, bom2, factor, addthis=True, level=level + 10)
        return result

