# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp

class PriceComponentType(models.Model):

    _name = 'dms.price.component'
    _description = 'Pricelist component Type'

    name = fields.Char('Price Component Name', required=True, index=True)
    description = fields.Char('Description', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)


class PricelistItemComponent(models.Model):
    _name = 'pricelist.component'

    type_id = fields.Many2one('dms.price.component',string='Component Type')
    item_id = fields.Many2one('product.pricelist.item',string='Pricelist Item')
    price = fields.Float(
        'Price', digits=dp.get_precision('Product Price'))
    mandatory = fields.Boolean('Mandatory', default=False)


class PricelistItem(models.Model):
     _name = 'product.pricelist.item'
     _inherit = 'product.pricelist.item'

     component = fields.One2many('pricelist.component', 'item_id', string='Pricelist component')
     component_based_price = fields.Float('Component Based Price', digits=dp.get_precision('Product Price'))
