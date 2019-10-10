# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
class account_payment(models.Model):
    _name = "account.payment"
    _inherit = 'account.payment'
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_payment_rel', 'payment_id', 'invoice_id',
                                   string="Invoices", copy=False, readonly=False)


class SaleAdvancePaymentInv(models.TransientModel):
    _name = "dms.booking.payment.inv"
    _description = "Sales booking Payment Receipt"
    _inherit = 'account.payment'

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        return self.env['product.product'].browse(int(product_id))

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id().property_account_income_id

    payment_type = fields.Selection(selection_add=[('transfer', 'Internal Transfer')],default='inbound')
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
        # # Create deposit product if necessary
        # if not self.product_id:
        #     vals = self._prepare_deposit_product()
        #     self.product_id = self.env['product.product'].create(vals)
        #     self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)
        # sale_line_obj = self.env['sale.order.line']
        # for order in sale_orders:
        #     amount = self.amount
        #     if self.product_id.invoice_policy != 'order':
        #         raise UserError(_(
        #             'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
        #     if self.product_id.type != 'service':
        #         raise UserError(_(
        #             "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
        #     taxes = self.product_id.taxes_id.filtered(
        #         lambda r: not order.company_id or r.company_id == order.company_id)
        #     if order.fiscal_position_id and taxes:
        #         tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
        #     else:
        #         tax_ids = taxes.ids
        #     context = {'lang': order.partner_id.lang}
        #     analytic_tag_ids = []
        #     for line in order.order_line:
        #         analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
        #     so_line = sale_line_obj.create({
        #         'name': _('Advance: %s') % (time.strftime('%m %Y'),),
        #         'price_unit': amount,
        #         'product_uom_qty': 0.0,
        #         'order_id': order.id,
        #         'discount': 0.0,
        #         'product_uom': self.product_id.uom_id.id,
        #         'product_id': self.product_id.id,
        #         'analytic_tag_ids': analytic_tag_ids,
        #         'tax_id': [(6, 0, tax_ids)],
        #         'is_downpayment': True,
        #         'qty_invoiced': 1,
        #     })
        #     del context
            # self._create_invoice(order,order_first_line, so_line, amount)
        inv = sale_orders.action_invoice_create(final=True)
        invoice = self.env['account.invoice'].search([('id','=',inv[0])])
        invoice.action_invoice_open()
        vals ={
            'name':invoice.move_name,
            'move_name':invoice.move_name,
            'amount': self.amount,
            'invoice_ids':[(6, 0, invoice.ids)],
            'communication': invoice.number,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'partner_bank_account_id': False,
            'partner_id': invoice.partner_id.id,
            'partner_type': "customer",
            'payment_date': self.dob,
            'payment_difference_handling': "open",
            'state':'draft',
            'payment_method_id': 1,
            'payment_token_id': False,
            'payment_type': "inbound"
        }
        payment = self.env['account.payment'].create(vals)
        payment.post()
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}


