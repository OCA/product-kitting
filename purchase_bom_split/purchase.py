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


class purchase_order(Model):

    _inherit = "purchase.order"

    def _prepare_order_line_split_move(self, cr, uid, order, base_line, component, picking_id, context=None):
        vals = super(purchase_order, self)._prepare_order_line_move(
            cr, uid, order, base_line, picking_id, context=context)
        vals.update({
            'name': ("PO: %s" % component['name'])[:250],
            'product_id': component['product_id'],
            'product_qty': component['product_qty'],
            'product_uom': component['product_uom'],
            'product_uos_qty': component['product_qty'],
            'product_uos': component['product_uos']
        })
        return vals

    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates pickings and appropriate stock moves for given order lines, then
        confirms the moves, makes them available, and confirms the picking.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        Inherited in order to explode BoMs in many move lines in the picking.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: list of IDs of pickings used/created for the given order lines (usually just one)
        """
        move_obj = self.pool.get('stock.move')
        bom_obj = self.pool.get('mrp.bom')
        picking_obj = self.pool.get('stock.picking')
        product_obj = self.pool.get('product.product')
        uom_obj = self.pool['product.uom']
        bom_order_lines = []
        normal_order_lines = order_lines[:]
        for line in order_lines:
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
        picking_id = False
        if bom_order_lines:
            picking_id = picking_obj.create(
                cr, uid, self._prepare_order_picking(cr, uid, order, context=context))

        new_move_ids = []
        for line, bom in bom_order_lines:
            factor = uom_obj._compute_qty_obj(cr, uid, line.product_uom, line.product_qty, bom.product_uom)
            bom_components = bom_obj.bom_split(
                cr, uid, bom, factor)

            move_dest_id = None
            for component in bom_components:
                product = product_obj.browse(
                    cr, uid, component['product_id'], context=context)
                # do not create a move for service products
                if product.type in ('product', 'consu'):
                    # if at least one stockable product
                    # update the order line destination move
                    move_dest_id = line.move_dest_id

                    vals = self._prepare_order_line_split_move(
                        cr, uid,
                        order,
                        line,
                        component,
                        picking_id,
                        context=context)
                    move_id = move_obj.create(cr, uid, vals, context=context)
                    new_move_ids.append(move_id)
            if move_dest_id:
                line.move_dest_id.write({'location_id': move_dest_id})

        move_obj.action_confirm(cr, uid, new_move_ids)
        move_obj.force_assign(cr, uid, new_move_ids)
        return super(purchase_order, self)._create_pickings(
            cr, uid, order, normal_order_lines, picking_id=picking_id, context=context)

