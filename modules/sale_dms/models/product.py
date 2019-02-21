from odoo import api, fields, models


class DmsProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    color_value = fields.Char('color', compute='_compute_color', help='test color')
    variant_value = fields.Char('variant', compute='_compute_variant', help='test something')

    @api.one
    @api.depends('attribute_value_ids')
    def _compute_color(self):
        for attribute_value in self.attribute_value_ids:
            if attribute_value.attribute_id.name == 'color':
                self.color_value = attribute_value.name

    @api.one
    @api.depends('attribute_value_ids')
    def _compute_variant(self):
        for attribute_value in self.attribute_value_ids:
            if attribute_value.attribute_id.name == 'variant':
                self.variant_value = attribute_value.name
