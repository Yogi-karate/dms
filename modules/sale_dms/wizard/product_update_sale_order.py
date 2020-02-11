# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductUpdateForSaleOrder(models.TransientModel):
    _name = "product.update.sale.order"
    _description = "Product Update For SaleOrder"

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(ProductUpdateForSaleOrder, self).default_get(fields)
        if self._context.get('active_id'):
            order = self.env['sale.order'].browse(self._context['active_id'])
            result['order_id'] = order.id
            print(fields)
            if order.pricelist_id:
                result['pricelist'] = order.pricelist_id.id
        return result

    order_id = fields.Many2one('sale.order', string='Sale Order')
    product_id = fields.Many2one('product.template', string='Product', required=True
                                 )
    product_color = fields.Many2one('product.attribute.value', required=True, string='Color')
    product_variant = fields.Many2one('product.attribute.value', required=True, string='Variant')

    variant_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                               compute='compute_variant_attribute_values')
    color_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                             compute='compute_color_attribute_values')
    pricelist = fields.Many2one('product.pricelist', string='Pricelist', required=True, ondelete="cascade")
    show_color = fields.Boolean('Color Visible', default=False)

    @api.onchange('product_id')
    def compute_variant_attribute_values(self):
        if self.variant_attribute_values or self.color_attribute_values:
            self.product_variant = False
            self.product_color = False
        self.variant_attribute_values = None
        self.color_attribute_values = None

        products = self.sudo().env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)])
        self.variant_attribute_values = products.mapped('attribute_value_ids').filtered(
            lambda attrib: attrib.attribute_id.name.lower() == 'variant')
        print(self.variant_attribute_values)

    @api.onchange('product_variant')
    def compute_color_attribute_values(self):
        if self.color_attribute_values:
            self.product_color = False
            self.color_attribute_values = None
        products = self.sudo().env['product.product'].search(
            [('product_tmpl_id', '=', self.product_id.id), ('variant_value', '=', self.product_variant.name)])
        self.color_attribute_values = products.mapped('attribute_value_ids')
        self.show_color = True
        print(self.color_attribute_values)

    @api.multi
    def action_apply(self):
        product = self.sudo().env['product.product'].search([('product_tmpl_id', '=', self.product_id.id),
                                                             ('color_value', '=', self.product_color.name),
                                                             ('variant_value', '=', self.product_variant.name)],
                                                            limit=1)
        if not product:
            raise UserError(_("This combiination does not exist!"))

        sale_order_line = self.sudo().env['sale.order.line'].search([('id', '=', self.order_id.order_line[0].id)])
        pricelist_item = self.sudo().env['product.pricelist.item'].search(
            [('product_id', '=', product.id), ('pricelist_id', '=', self.pricelist.id)])
        sale_order_line.write(
            {'product_id': product.id, 'price_unit': pricelist_item.fixed_price, 'name': self.product_id.name})
        account_invoice_line = self.sudo().env['account.invoice.line'].search(
            [('id', '=', sale_order_line.invoice_lines.id)])
        account_invoice_line.write(
            {'product_id': product.id, 'price_unit': pricelist_item.fixed_price, 'name': self.product_id.name,
             'discount_price': sale_order_line.discount_price})
        stock_move = self.sudo().env['stock.move'].search([('sale_line_id', '=', sale_order_line.id)])
        stock_move.write({'product_id': product.id, 'name': product.name})
        if len(self.order_id.picking_ids) < 1:
            return
        picking = self.order_id.picking_ids[0]
        if picking:
            picking.do_unreserve()
