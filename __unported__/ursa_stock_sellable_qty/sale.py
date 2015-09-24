# -*- coding: utf-8 -*-

######################################################################
#
#  Note: Program metadata is available in /__init__.py
#
######################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval as eval
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round, float_compare
import logging

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    def product_id_change_sell_qty(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, warehouse_id=False, context=None):

        context = context or {}
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        warehouse_obj = self.pool['stock.warehouse']
        warning = {}

        res = self.product_id_change_with_wh(cr, uid, ids, pricelist, product, qty=qty,uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, warehouse_id=warehouse_id, context=context)

        #update of result obtained in super function
        product_obj = product_obj.browse(cr, uid, product, context=context)

        warning_msgs = False
        
        if product_obj.type == 'product':
            #determine if the product is MTO or not (for a further check)
            isMto = False
            if warehouse_id:
                warehouse = warehouse_obj.browse(cr, uid, warehouse_id, context=context)
                for product_route in product_obj.route_ids:
                    if warehouse.mto_pull_id and warehouse.mto_pull_id.route_id and warehouse.mto_pull_id.route_id.id == product_route.id:
                        isMto = True
                        break
            else:
                try:
                    mto_route_id = warehouse_obj._get_mto_route(cr, uid, context=context)
                except:
                    # if route MTO not found in ir_model_data, we treat the product as in MTS
                    mto_route_id = False
                if mto_route_id:
                    for product_route in product_obj.route_ids:
                        if product_route.id == mto_route_id:
                            isMto = True
                            break                    
            
            #check if product is available, and if not: raise a warning, but do this only for products that aren't processed in MTO
            if not isMto:
                uom_record = False
                if uom:
                    uom_record = product_uom_obj.browse(cr, uid, uom, context=context)
                    if product_obj.uom_id.category_id.id != uom_record.category_id.id:
                        uom_record = False
                if not uom_record:
                    uom_record = product_obj.uom_id
                compare_qty = float_compare(product_obj.qty_sellable, qty, precision_rounding=uom_record.rounding)
                if compare_qty == -1:
                    warn_msg = _('%s (%s):\nQty on Sale Order: %.2f\nQuantity available: %.2f\nQuantity reserved: %.2f\nAvailable to sell: %.2f') % \
                        (product_obj.name, uom_record.name, qty,
                         max(0,product_obj.qty_available),
                         max(0,product_obj.qty_available - product_obj.qty_sellable),
                         max(0,product_obj.qty_sellable))
                    warning_msgs = warn_msg + "\n\n"

        #update of warning messages
        if warning_msgs:
            warning = {
                       'title': _('Not Enough Stock Warning!'),
                       'message' : warning_msgs
                    }
        res.update({'warning': warning})
        return res
 
    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

