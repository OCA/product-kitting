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
from openerp.tools.float_utils import float_round
import logging

class product_product(osv.osv):
    _inherit = "product.product"
        
    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        context = context or {}
        field_names = field_names or []

        domain_products = [('product_id', 'in', ids)]
        domain_quant, domain_move_in, domain_move_out = self._get_domain_locations(cr, uid, ids, context=context)
        domain_move_in += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_move_out += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
        domain_quant += domain_products
        if context.get('lot_id') or context.get('owner_id') or context.get('package_id'):
            if context.get('lot_id'):
                domain_quant.append(('lot_id', '=', context['lot_id']))
            if context.get('owner_id'):
                domain_quant.append(('owner_id', '=', context['owner_id']))
            if context.get('package_id'):
                domain_quant.append(('package_id', '=', context['package_id']))
            moves_in = []
            moves_out = []
        else:
            moves_in = self.pool.get('stock.move').read_group(cr, uid, domain_move_in, ['product_id', 'product_qty'], ['product_id'], context=context)
            moves_out = self.pool.get('stock.move').read_group(cr, uid, domain_move_out, ['product_id', 'product_qty'], ['product_id'], context=context)

        quants = self.pool.get('stock.quant').read_group(cr, uid, domain_quant, ['product_id', 'qty'], ['product_id'], context=context)
        quants = dict(map(lambda x: (x['product_id'][0], x['qty']), quants))

        moves_in = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_in))
        moves_out = dict(map(lambda x: (x['product_id'][0], x['product_qty']), moves_out))
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            id = product.id
            qty_available = float_round(quants.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            incoming_qty = float_round(moves_in.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            outgoing_qty = float_round(moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            virtual_available = float_round(quants.get(id, 0.0) + moves_in.get(id, 0.0) - moves_out.get(id, 0.0), precision_rounding=product.uom_id.rounding)
            res[id] = {
                'qty_available': qty_available,
                'incoming_qty': incoming_qty,
                'outgoing_qty': outgoing_qty,
                'virtual_available': virtual_available,
                'qty_sellable': max(0,qty_available - outgoing_qty),
            }
            
        return res

    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        res = []
        for field, operator, value in domain:
            #to prevent sql injections
            assert field in ('qty_available', 'qty_sellable','virtual_available', 'incoming_qty', 'outgoing_qty'), 'Invalid domain left operand'
            assert operator in ('<', '>', '=', '!=', '<=', '>='), 'Invalid domain operator'
            assert isinstance(value, (float, int)), 'Invalid domain right operand'

            if operator == '=':
                operator = '=='

            product_ids = self.search(cr, uid, [], context=context)
            ids = []
            if product_ids:
                #TODO: use a query instead of this browse record which is probably making the too much requests, but don't forget
                #the context that can be set with a location, an owner...
                for element in self.browse(cr, uid, product_ids, context=context):
                    if eval(str(element[field]) + operator + str(value)):
                        ids.append(element.id)
            res.append(('id', 'in', ids))
        return res

    def _product_sellable_text(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = str(product.qty_sellable) +  _(" You Can Sell")
        return res

    _columns = {
        'qty_available': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Quantity On Hand',
            fnct_search=_search_product_quantity,
            help="Current quantity of products.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'virtual_available': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Forecast Quantity',
            fnct_search=_search_product_quantity,
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming)\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored in this location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'incoming_qty': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Incoming',
            fnct_search=_search_product_quantity,
            help="Quantity of products that are planned to arrive.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods arriving to this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods arriving to the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "Otherwise, this includes goods arriving to any Stock "
                 "Location with 'internal' type."),
        'outgoing_qty': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Outgoing',
            fnct_search=_search_product_quantity,
            help="Quantity of products that are planned to leave.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods leaving this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods leaving the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "Otherwise, this includes goods leaving any Stock "
                 "Location with 'internal' type."),   
        'qty_sellable_text': fields.function(_product_sellable_text, type='char'),
        'qty_sellable': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Quantity You Can Sell',
            fnct_search=_search_product_quantity,
            help="Current quantity of products you can Sell.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type.  Anything not commited to an existing Sale is counted."),
    }


class product_template(osv.osv):
    _name = 'product.template'
    _inherit = 'product.template'

    def _product_available(self, cr, uid, ids, name, arg, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            sumq = 0
            for p in product.product_variant_ids:
                sumq += p.qty_available
            res[product.id] = {
                # "reception_count": sum([p.reception_count for p in product.product_variant_ids]),
                # "delivery_count": sum([p.delivery_count for p in product.product_variant_ids]),
                "qty_available": sum([p.qty_available for p in product.product_variant_ids]) or 0,
                "virtual_available": sum([p.virtual_available for p in product.product_variant_ids]) or 0,
                "incoming_qty": sum([p.incoming_qty for p in product.product_variant_ids]) or 0,
                "outgoing_qty": sum([p.outgoing_qty for p in product.product_variant_ids]) or 0,                
                "qty_sellable": sum([p.qty_sellable for p in product.product_variant_ids]) or 0,
            }        
        return res


    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        prod = self.pool.get("product.product")
        res = []
        for field, operator, value in domain:
            #to prevent sql injections
            assert field in ('qty_sellable','qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty'), 'Invalid domain left operand'
            assert operator in ('<', '>', '=', '!=', '<=', '>='), 'Invalid domain operator'
            assert isinstance(value, (float, int)), 'Invalid domain right operand'

            if operator == '=':
                operator = '=='

            product_ids = prod.search(cr, uid, [], context=context)
            ids = []
            if product_ids:
                #TODO: use a query instead of this browse record which is probably making the too much requests, but don't forget
                #the context that can be set with a location, an owner...
                for element in prod.browse(cr, uid, product_ids, context=context):
                    if eval(str(element[field]) + operator + str(value)):
                        ids.append(element.id)
            res.append(('product_variant_ids', 'in', ids))
        return res

    
    _columns = {
        'qty_available': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Quantity On Hand'),
        'virtual_available': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Quantity Available'),
        'incoming_qty': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Incoming'),
        'outgoing_qty': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Outgoing'),    
        'qty_sellable': fields.function(_product_available, multi='qty_available',
            fnct_search=_search_product_quantity, type='float', string='Quantity You Can Sell'),
    }


    # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

