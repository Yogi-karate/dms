# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _name = "dms.booking.payment.inv"
    _description = "Sales booking Payment Receipt"

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        return self.env['product.product'].browse(int(product_id))

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id().property_account_income_id

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'On-Hold'),
        ('2', 'Medium'),
        ('3', 'High'),
    ])
    dob = fields.Datetime('Date of Booking', default=fields.Datetime.now)
    amount = fields.Float('Down Payment Amount', digits=dp.get_precision('Account'),
                          help="The amount to be invoiced in advance, taxes excluded.")
    product_id = fields.Many2one('product.product', string='Down Payment Product', domain=[('type', '=', 'service')],
                                 default=_default_product_id)

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        sale_orders.write({'state': 'booked', 'priority': self.priority, 'dob': self.dob})
        # Create deposit product if necessary
        if not self.product_id:
            vals = self._prepare_deposit_product()
            self.product_id = self.env['product.product'].create(vals)
            self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)
        sale_line_obj = self.env['sale.order.line']
        for order in sale_orders:
            amount = self.amount
            if self.product_id.invoice_policy != 'order':
                raise UserError(_(
                    'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
            if self.product_id.type != 'service':
                raise UserError(_(
                    "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
            taxes = self.product_id.taxes_id.filtered(
                lambda r: not order.company_id or r.company_id == order.company_id)
            if order.fiscal_position_id and taxes:
                tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
            else:
                tax_ids = taxes.ids
            context = {'lang': order.partner_id.lang}
            analytic_tag_ids = []
            for line in order.order_line:
                analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
            so_line = sale_line_obj.create({
                'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                'price_unit': amount,
                'product_uom_qty': 0.0,
                'order_id': order.id,
                'discount': 0.0,
                'product_uom': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'analytic_tag_ids': analytic_tag_ids,
                'tax_id': [(6, 0, tax_ids)],
                'is_downpayment': True,
                'qty_invoiced': 1,
            })
            del context
            # self._create_invoice(order,order_first_line, so_line, amount)
        sale_orders.action_invoice_create(so_line, final=True)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.deposit_account_id.id,
            'taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
            'company_id': False,
        }
