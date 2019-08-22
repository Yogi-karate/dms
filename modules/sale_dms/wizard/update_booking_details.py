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
    ], string='Finance Type', store=True, default='in')
    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    payment_date = fields.Datetime('Payment Date')
    delivery_date = fields.Datetime('Delivery Date')

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the leads/opps to merge.
            In order to get merged, these leads/opps can't be in 'Dead' or 'Closed'
        """
        result = super(UpdateBookingDetails, self).default_get(fields)

        if self._context.get('active_id'):
            order = self.env['sale.order'].browse(self._context['active_id'])
            print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
            if order.finance_type:
                    result['finance_type'] = order.finance_type
            if order.financier_name:
                    result['financier_name'] = order.financier_name
            if order.payment_date:
                    result['payment_date'] = order.payment_date
            if order.delivery_date:
                result['delivery_date'] = order.delivery_date

            print(order)
            print(result)
            print(fields)
            print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")

            print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")

        return result


    @api.multi
    def action_reassign(self):
        self.ensure_one()
        print("Hello from reassign")
