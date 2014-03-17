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

import netsvc
from osv.orm import Model


class sale_order(Model):

    _inherit = "sale.order"

    def _prepare_order_line_split_procurement(self, cr, uid, order, base_line,
                                              component, move_id, date_planned, context=None):
        vals = super(sale_order, self)._prepare_order_line_procurement(
            cr, uid, order, base_line, move_id, date_planned, context=context)
        vals.update({
            'name': ("SO: %s" % component['name'])[:250],
            'product_id': component['product_id'],
            'product_qty': component['product_qty'],
            'product_uom': component['product_uom'],
            'product_uos_qty': component['product_qty'],
            'product_uos': component['product_uos']
        })
        return vals

    def _prepare_order_line_split_move(self, cr, uid, order, base_line, component, picking_id, date_planned, context=None):
        vals = super(sale_order, self)._prepare_order_line_move(
            cr, uid, order, base_line, picking_id, date_planned, context=context)
        vals.update({
            'name': ("SO: %s" % component['name'])[:250],
            'product_id': component['product_id'],
            'product_qty': component['product_qty'],
            'product_uom': component['product_uom'],
            'product_uos_qty': component['product_qty'],
            'product_uos': component['product_uos']
        })
        return vals

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Create the required procurements to supply sale order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sale order's requested location.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        Inherited in order to explode BoMs in many move lines in the picking.

        :param browse_record order: sale order to which the order lines belong
        :param list(browse_record) order_lines: sale order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        move_obj = self.pool.get('stock.move')
        bom_obj = self.pool.get('mrp.bom')
        picking_obj = self.pool.get('stock.picking')
        product_obj = self.pool.get('product.product')
        procurement_obj = self.pool.get('procurement.order')

        bom_order_lines = []
        normal_order_lines = order_lines[:]
        for line in order_lines:
            if line.state == 'done':
                continue
            if not line.product_id:
                continue
            bom_id = bom_obj._bom_find(
                cr, uid, line.product_id.id, line.product_uom.id)
            if not bom_id:
                continue
            # extract lines with a phantom bom, they need
            # a special handling (explode bom and create
            # a move line per component)
            bom = bom_obj.browse(cr, uid, bom_id, context=context)
            if bom.type == 'phantom':
                bom_order_lines.append((line, bom))
                normal_order_lines.remove(line)

        # if we have at least one line which have to be split
        # we prepare the picking so we'll be able to bind it
        # to the move lines
        if bom_order_lines and not picking_id:
            picking_id = picking_obj.create(
                cr, uid, self._prepare_order_picking(cr, uid, order, context=context))

        proc_ids = []
        for line, bom in bom_order_lines:
            factor = line.product_uom_qty * line.product_uom.factor / bom.product_uom.factor
            bom_components = bom_obj.bom_split(
                cr, uid, bom, factor / bom.product_qty)

            date_planned = self._get_date_planned(
                cr, uid, order, line, order.date_order, context=context)

            first_component = None
            for component in bom_components:
                product = product_obj.browse(
                    cr, uid, component['product_id'], context=context)
                # do not create a move for service products
                move_id = False
                if product.type in ('product', 'consu'):
                    vals = self._prepare_order_line_split_move(
                        cr, uid,
                        order,
                        line,
                        component,
                        picking_id,
                        date_planned,
                        context=context)
                    move_id = move_obj.create(cr, uid, vals, context=context)

                proc_vals = self._prepare_order_line_split_procurement(
                    cr, uid, order, line, component, move_id, date_planned, context=context)
                proc_id = procurement_obj.create(
                    cr, uid, proc_vals, context=context)

                proc_ids.append(proc_id)
                if first_component is None:
                    first_component = (move_id, proc_id)

            # The sale order line could be linked only
            # to 1 procurement, so we link it with
            # the first procurement.
            line.write({'procurement_id': first_component[1]})
            self.ship_recreate(cr, uid, order, line, first_component[0], first_component[1])

        res = super(sale_order, self)._create_pickings_and_procurements(
            cr, uid, order, normal_order_lines, picking_id=picking_id, context=context)

        wf_service = netsvc.LocalService("workflow")
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        return res

