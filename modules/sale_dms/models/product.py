from odoo import api, fields, models

class DmsProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel')
    ], string='Fuel',
        default='petrol')

    color_value = fields.Char('color', compute='_compute_color', help='test color', store=True)
    variant_value = fields.Char('variant', compute='_compute_variant', help='test something', store=True)

    @api.one
    @api.depends('attribute_value_ids')
    def _compute_color(self):
        for attribute_value in self.attribute_value_ids:
            if attribute_value.attribute_id.name.lower() == 'color':
                self.color_value = attribute_value.name

    @api.one
    @api.depends('attribute_value_ids')
    def _compute_variant(self):
        for attribute_value in self.attribute_value_ids:
            if attribute_value.attribute_id.name.lower() == 'variant':
                self.variant_value = attribute_value.name

class DMSProductAttribute(models.Model):
        _name = 'product.attribute'
        _inherit = 'product.attribute'

        company_id = fields.Many2one('res.company')
        active = fields.Boolean(default=True)


class DMSProductAttributeValue(models.Model):
    _name = 'product.attribute.value'
    _inherit = 'product.attribute.value'

    company_id = fields.Many2one('res.company')
    active = fields.Boolean(default=True)