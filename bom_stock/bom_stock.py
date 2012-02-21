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

from osv import fields, osv
from tools.translate import _

class rescompany(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'ref_stock': fields.selection([('real', 'Real Stock'),('virtual','Virtual Stock'), ('immediately','Immediately Usable Stock')], 'Reference stock')
    }
    _defaults = {
        'ref_stock': lambda *a: 'real'         
    }    
rescompany()    
        

class product_bom_stock_value(osv.osv):
    """
    Inherit Product in order to add an "Bom Stock" field
    """
    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        # We need available, virtual or immediately usable   quantity which is selected from company to compute Bom stock Value
        # so we add them in the calculation.
        bom_obj = self.pool.get('mrp.bom')
        user_obj = self.pool.get('res.users')
        comp_obj = self.pool.get('res.company')
        if 'bom_stock' in field_names:
            field_names.append('qty_available')
            field_names.append('immediately_usable_qty')
            field_names.append('virtual_available')

        res = super(product_bom_stock_value, self)._product_available(cr, uid, ids, field_names, arg, context)

        if 'bom_stock' in field_names:
            comp = user_obj.browse(cr, uid ,uid , context=context).company_id
            if not comp:
                comp_id = comp_obj.search(cr, uid, [], context=context)[0]
                comp = comp_obj.browse(cr, uid, comp_id, context=context)

            for product_id, stock_qty in res.iteritems():
                prod_min_quantities = []
                product_qty = False
                if comp.ref_stock == 'real':
                    product_qty = stock_qty.get('qty_available', 0.0)
                elif comp.ref_stock == 'virtual':
                    product_qty = stock_qty.get('virtual_available', 0.0)
                elif comp.ref_stock == 'immediately':
                    product_qty = stock_qty.get('immediately_usable_qty', 0.0)

                product = self.browse(cr, uid, product_id, context=context)
                bom_ids = bom_obj._bom_find(cr, uid, product.id, product.uom_id.id, properties=[])
                res[product_id]['bom_stock'] = product_qty
                if bom_ids:
                    bom = bom_obj.browse(cr, uid, bom_ids, context=context)
                    if bom.bom_lines:
                        stop_compute_bom = False
                        # Compute stock qty of each product used in the BoM and get the minimal number of items we can produce with them
                        for line in bom.bom_lines:
                            bom_qty = False
                            prod_min_quantity = 0.0
                            if comp:
                                if comp.ref_stock == 'real':
                                    bom_qty = line.product_id.qty_available
                                elif comp.ref_stock == 'virtual':
                                    bom_qty = line.product_id.virtual_available
                                else:
                                    bom_qty = line.product_id.immediately_usable_qty

                            if bom_qty and bom_qty >= line.product_qty:
                                prod_min_quantity = (bom_qty * line.product_id.uom_id.factor / line.product_uom.factor) / line.product_qty
                            else:  # if one product has not enough stock, BoM stock must be 0
                                stop_compute_bom = True

                            prod_min_quantities.append(prod_min_quantity)

                            if stop_compute_bom:
                                break

                if prod_min_quantities:
                    res[product_id]['bom_stock'] =  product_qty + sorted(prod_min_quantities)[0]
        return res
    
    _inherit = 'product.product'
    _columns = {
        'qty_available': fields.function(_product_available,
                                         method=True,
                                         type='float',
                                         string='Real Stock',
                                         help="Current quantities of products in selected locations or all internal if none have been selected.",
                                         multi='qty_available'),
        'virtual_available': fields.function(_product_available,
                                             method=True,
                                             type='float',
                                             string='Virtual Stock',
                                             help="Futur stock for this product according to the selected location or all internal if none have been selected. Computed as: Real Stock - Outgoing + Incoming.",
                                             multi='qty_available'),
        'incoming_qty': fields.function(_product_available,
                                        method=True,
                                        type='float',
                                        string='Incoming',
                                        multi='qty_available',
                                        help="Quantities of products that are planned to arrive in selected locations or all internal if none have been selected."),        
        'outgoing_qty': fields.function(_product_available,
                                        method=True,
                                        type='float',
                                        string='Outgoing',
                                        multi='qty_available',
                                        help="Quantities of products that are planned to leave in selected locations or all internal if none have been selected."),
        'immediately_usable_qty': fields.function(_product_available,
                                                  method=True, type='float',
                                                  string='Immediately Usable Stock',
                                                  help="Quantities of products really available for sale. Computed as: Real Stock - Outgoing.",
                                                  multi='qty_available'),
        'bom_stock': fields.function(_product_available,
                                     method=True,
                                     type='float',
                                     string='BoM Stock Value',
                                     help="Quantities of products,  useful to know how much of this product you could have. Computed as:  (Reference stock of This product + How much could I produce of this product)",
                                     multi='qty_available'),
    }
    
product_bom_stock_value()
