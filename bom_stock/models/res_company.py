# -*- coding: utf-8 -*-
# © 2015 Camptocamp SA, Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    ref_stock = fields.Selection(
        [('real', 'Real Stock'),
         ('virtual', 'Virtual Stock'),
         ('immediately', 'Immediately Usable Stock')],
        'Reference Stock for BoM Stock', default='real')
