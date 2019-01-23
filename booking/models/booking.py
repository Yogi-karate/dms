# -*- coding: utf-8 -*-
# Part of Saboo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class BookingOrder(models.Model):

    _name = "booking.order"
    _description = "Vehicle Booking Order"
    _order = 'date_order desc, id desc'
    _inherit = "sale.order"

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    booking_amount = fields.Monetary(string='booking amount', store=True, readonly=True,
                                   track_visibility='always', track_sequence=6)
    order_id = fields.Many2one(
        'sale.order', 'SaleOrder',
        domain=[('state', 'in', ['draft'])], required=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True, compute='_get_customer')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'booking.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('booking.order') or _('New')
        result = super(BookingOrder, self).create(vals)
        return result

    @api.multi
    def _write(self, values):
        res = super(BookingOrder, self)._write(values)
        return res

    @api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
        })


    @api.multi
    def _action_confirm(self):
        """ Implementation of additionnal mecanism of Sales Order confirmation.
            This method should be extended when the confirmation should generated
            other documents. In this method, the SO are in 'sale' state (not yet 'done').
        """
       # if self.env.context.get('send_email'):
       #     self.force_quotation_send()

        # create an analytic account if at least an expense product
        if any([expense_policy != 'no' for expense_policy in self.order_line.mapped('product_id.expense_policy')]):
            if not self.analytic_account_id:
                self._create_analytic_account()

        return True

    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'confirmed',
            'confirmation_date': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can not delete a confirmed booking. You must first cancel it.'))
        return super(BookingOrder, self).unlink()

    @api.one
    def _get_customer(self):
        # We only care for the customer if sale order is entered.
        if self.order_id:
            customer_id = self.order_id.partner_id
            self.customer_id = customer_id