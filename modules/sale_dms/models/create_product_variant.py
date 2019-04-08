from odoo import api, fields, models
from odoo.exceptions import UserError



class DmsProduct(models.TransientModel):
    _name = 'dms.product'

    product_id = fields.Many2one('product.template', string='Product', ondelete="cascade")
    product_color = fields.Many2one('product.attribute.value', string='Color')
    product_variant = fields.Many2one('product.attribute.value', string='Variant')
    show_color = fields.Boolean('Color Visible', default=False)
    color_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                             compute='compute_color_attribute_values')
    name = fields.Char(string='name',compute='_compute_name')

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        res = super(DmsProduct, self).create(vals)
        res.create_product_variant()
        return res

    @api.onchange('product_variant')
    def compute_color_attribute_values(self):
        products = self.sudo().env['product.product'].search(
            [('product_tmpl_id', '=', self.product_id.id), ('variant_value', '=', self.product_variant.name)])
        for x in products:
            print(x.id, "_____" + x.name + "_____" + x.variant_value + "___" + x.color_value)
        self.color_attribute_values = products.mapped('attribute_value_ids')
        self.show_color = True
        print(self.color_attribute_values)
    @api.one
    @api.depends('product_id')
    def _compute_name(self):
        self.name = self.product_id.name +"(" +self.product_color.name +","+ self.product_variant.name+")"



    @api.multi
    def create_product_variant(self):
        product = self.env['product.product']
        vals = {
            'name': self.product_id.name,
            'company_id': False,
            'product_tmpl_id': self.product_id.id,
            'attribute_value_ids': [(6, '_', [self.product_color.id, self.product_variant.id])]
        }
        exiting_product= self.sudo().env['product.product'].search(
            [('product_tmpl_id', '=', self.product_id.id), ('variant_value', '=', self.product_variant.name) ,('color_value','=',self.product_color.name)])
        if not exiting_product:
                 product.create(vals)
        else:
            raise UserError(_("Unable to Create as product already exists"))
        print("***************************************************************88")
        print(self.product_id.name)
        print(self.product_color.id)
        print(self.product_variant.id)
