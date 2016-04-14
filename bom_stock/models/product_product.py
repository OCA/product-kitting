# -*- coding: utf-8 -*-
# © 2015 Camptocamp SA, Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp

BOM_STOCK_MAPPING = {
    'real': 'qty_available',
    'virtual': 'virtual_available',
    'immediately': 'immediately_usable_qty'
}


class Product(models.Model):
    _inherit = 'product.product'

    @api.one
    def _compute_bom_stock(self):
        bom_obj = self.env['mrp.bom']
        uom_obj = self.env['product.uom']
        company = self.env.user.company_id
        if not company:
            company = self.env['res.company'].search([])[0]
        stock_field = BOM_STOCK_MAPPING[company.ref_stock]
        product_qty = 0.0
        bom_id = bom_obj._bom_find(product_id=self.id, properties=[])
        if bom_id:
            prod_min_quantities = []
            bom = bom_obj.browse(bom_id)
            product_qty = bom.product_id[stock_field]
            if bom.bom_line_ids:
                stop_compute_bom = False
                for line in bom.bom_line_ids:
                    prod_min_quantity = 0.0
                    bom_qty = line.product_id[stock_field]
                    line_product_qty = uom_obj._compute_qty_obj(
                        line.product_uom,
                        line.product_qty,
                        line.product_id.uom_id,)
                    if bom_qty >= line_product_qty:
                        prod_min_quantity = bom_qty / line_product_qty
                    else:
                        stop_compute_bom = True
                    prod_min_quantities.append(prod_min_quantity)
                    if stop_compute_bom:
                        break
                produced_qty = uom_obj._compute_qty_obj(
                    bom.product_uom,
                    bom.product_qty,
                    bom.product_tmpl_id.uom_id)
                product_qty += min(prod_min_quantities) * produced_qty
            self.bom_stock = product_qty

    bom_stock = fields.Float(
        string="Bill of Materials Stock",
        compute='_compute_bom_stock',
        digits_compute=dp.get_precision('Product UoM'))
