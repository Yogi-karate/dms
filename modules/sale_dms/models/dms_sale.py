# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode


class DmsSaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('booked', 'Booked'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'On-Hold'),
        ('2', 'Medium'),
        ('3', 'High'),
    ])
    stock_status = fields.Selection([
        ('allotted', 'Allotted'),
        ('not-allotted', 'Not-Allotted'),
        ], string='Status', compute='_calculate_product', default='not-allotted')
    dob = fields.Datetime('Date of Booking')
    product_name = fields.Char('Model',compute='_calculate_product')
    product_variant = fields.Char('Variant',compute='_calculate_product')
    product_color = fields.Char('Color',compute='_calculate_product')

    def _calculate_product(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'draft' or pick.state == 'confirmed' or pick.state == 'waiting':
                    order.stock_status = 'not-allotted'
                else:
                    order.stock_status = 'allotted'
            count = 0
            for x in order.order_line:
                if count > 0:
                    break
                count += 1
                print(x.product_id)
                order.product_name = x.product_id.name
                order.product_variant = x.product_id.variant_value
                order.product_color = x.product_id.color_value
                print("000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

    @api.multi
    def _write(self, values):
        """ Override of private write method in order to generate activities
        based in the invoice status. As the invoice status is a computed field
        triggered notably when its lines and linked invoice status changes the
        flow does not necessarily goes through write if the action was not done
        on the SO itself. We hence override the _write to catch the computation
        of invoice_status field. """
        print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        print(values)
        print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",self.team_id.location_id.name)
        location_name = self.team_id.location_id.name
        if not location_name:
            print("no location")
        else:
            if 'state' in values and values['state'] == 'booked':
                    if 'Tirumalgiri' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.tir') or _('New')
                    if 'Mettuguda' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.met') or _('New')
                    if 'Ranigunj' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.rani') or _('New')

        # if values.get('name', _('New')) == _('New'):
        #     if 'company_id' in vals:
        #         values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code('sale.order') or _('New')
        #     else:
        #         values['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
        if self.env.context.get('mail_activity_automation_skip'):
            return super(DmsSaleOrder, self)._write(values)

        if 'invoice_status' in values:
            if values['invoice_status'] == 'upselling':
                filtered_self = self.search([('id', 'in', self.ids),
                                             ('user_id', '!=', False),
                                             ('invoice_status', '!=', 'upselling')])
                filtered_self.activity_unlink(['sale.mail_act_sale_upsell'])
                for order in filtered_self:
                    order.activity_schedule(
                        'sale.mail_act_sale_upsell',
                        user_id=order.user_id.id,
                        note=_(
                            "Upsell <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer <a href='#' data-oe-model='%s' data-oe-id='%s'>%s</a>") % (
                                 order._name, order.id, order.name,
                                 order.partner_id._name, order.partner_id.id, order.partner_id.display_name))

        return super(DmsSaleOrder, self)._write(values)


class DmsSaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = 'sale.order.line'

    discount_price = fields.Float('Discount', digits=dp.get_precision('Product Price'), default=0.0)

    @api.depends('product_uom_qty', 'discount_price', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit - (line.discount_price or 0.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('price_unit', 'discount_price')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit - line.discount_price
