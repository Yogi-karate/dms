# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class UpdateBookingDetails(models.TransientModel):
    """
        Update Booking fields
    """

    _name = 'update.booking.details'
    _description = 'reassign enquiries to another user'
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
        ('cash','Cash'),
    ], string='Finance Type', store=True, default='in')
    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    finance_pmt = fields.Float('Finance Amount')
    finance_payment_date = fields.Date('Finance Payment Date')
    margin_pmt = fields.Float('Margin Money Amount')
    margin_payment_date = fields.Date('Margin Money Payment Date')
    delivery_date = fields.Date('Delivery Date')

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the leads/opps to merge.
            In order to get merged, these leads/opps can't be in 'Dead' or 'Closed'
        """
        result = super(UpdateBookingDetails, self).default_get(fields)
        if self._context.get('active_id'):
            order = self.env['sale.order'].browse(self._context['active_id'])
            if order.finance_type:
                result['finance_type'] = order.finance_type
            if order.financier_name:
                result['financier_name'] = order.financier_name.id
            if order.finance_payment_date:
                result['finance_payment_date'] = order.finance_payment_date
            if order.margin_pmt:
                result['margin_pmt'] = order.margin_pmt
            if order.margin_payment_date:
                result['margin_payment_date'] = order.margin_payment_date
            if order.finance_pmt:
                result['finance_pmt'] = order.finance_pmt
            if order.delivery_date:
                result['delivery_date'] = order.delivery_date
        return result

    @api.multi
    def action_update(self):
        self.ensure_one()
        print("Hello from reassign")
        sale_order = self.env['sale.order'].browse(self._context.get('active_ids', []))[0]
        if len(sale_order) > 1:
            return
        sale_order.write(
            {'finance_type': self.finance_type,
             'financier_name': self.financier_name.id,
             'finance_payment_date': self.finance_payment_date,
             'finance_pmt': self.finance_pmt,
             'margin_pmt': self.margin_pmt,
             'margin_payment_date': self.margin_payment_date,
             'delivery_date': self.delivery_date})
