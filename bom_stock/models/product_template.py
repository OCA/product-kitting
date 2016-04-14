# -*- coding: utf-8 -*-
# © 2015 Camptocamp SA, Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.one
    def _compute_bom_stock(self):
        self.bom_stock = sum(
            self.mapped('product_variant_ids').mapped('bom_stock'))

    bom_stock = fields.Float(
        string="Bill of Materials Stock",
        compute='_compute_bom_stock',
        digits_compute=dp.get_precision('Product UoM'))
