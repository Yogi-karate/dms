# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _name = "dms.booking.payment.inv"
    _description = "Sales booking Payment Receipt"
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'On-Hold'),
        ('2', 'Medium'),
        ('3', 'High'),
    ])
    dob = fields.Date('Date of Booking', default=fields.Date.today())
    amount = fields.Float('Down Payment Amount', help="The amount to be invoiced in advance, taxes excluded.")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    communication = fields.Char(string='Memo')


    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        sale_orders.write({'state': 'booked', 'priority': self.priority, 'dob': self.dob})
        inv = sale_orders.action_invoice_create(final=True)
        invoice = self.env['account.invoice'].search([('id', '=', inv[0])])
        invoice.action_invoice_open()
        vals = {
            'name': invoice.move_name,
            'move_name': invoice.move_name,
            'amount': self.amount,
            'invoice_ids': [(6, 0, invoice.ids)],
            'communication': invoice.communication,
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'partner_bank_account_id': False,
            'partner_id': invoice.partner_id.id,
            'partner_type': "customer",
            'payment_date': self.dob,
            'payment_difference_handling': "open",
            'state': 'draft',
            'payment_method_id': 1,
            'payment_token_id': False,
            'payment_type': "inbound"
        }
        payment = self.env['account.payment'].create(vals)
        payment.post()
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
