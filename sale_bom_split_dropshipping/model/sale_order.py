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

from openerp.osv import orm


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    def _create_components_procurements_direct_mto(self, cr, uid, order,
                                                   order_lines, context=None):
        proc_obj = self.pool['procurement.order']
        uom_obj = self.pool['product.uom']
        bom_obj = self.pool['mrp.bom']

        proc_ids = []
        for line, bom in order_lines:
            factor = uom_obj._compute_qty_obj(cr, uid,
                                              line.product_uom,
                                              line.product_uom_qty,
                                              bom.product_uom)
            bom_components = bom_obj.bom_split(cr, uid, bom, factor)

            date_planned = self._get_date_planned(
                cr, uid, order, line, order.date_order, context=context)

            first_component = None
            for component in bom_components:
                vals = self._prepare_order_line_split_procurement(
                    cr, uid, order, line, component,
                    False, date_planned, context=context
                )
                proc_id = proc_obj.create(cr, uid, vals, context=context)
                proc_ids.append(proc_id)
                if first_component is None:
                    first_component = proc_id

            # The sale order line could be linked only
            # to 1 procurement, so we link it with
            # the first procurement.
            line.write({'procurement_id': first_component})
        return proc_ids

    def _create_components_moves_and_procurements(self, cr, uid, order,
                                                  order_lines,
                                                  picking_id=False,
                                                  context=None):
        normal_lines = []
        dropship_lines = []
        dropship_flows = ('direct_delivery', 'direct_invoice_and_delivery')
        for line, bom in order_lines:
            if (line.type == 'make_to_order' and
                    line.sale_flow in dropship_flows):
                dropship_lines.append((line, bom))
            else:
                normal_lines.append((line, bom))
        proc_ids = self._create_components_procurements_direct_mto(
            cr, uid, order,
            dropship_lines,
            context=context
        )

        _super = super(SaleOrder, self)
        _super_create = _super._create_components_moves_and_procurements
        new_proc_ids, picking_id = _super_create(
            cr, uid, order, normal_lines,
            picking_id=picking_id, context=context
        )
        proc_ids += new_proc_ids
        return proc_ids, picking_id
