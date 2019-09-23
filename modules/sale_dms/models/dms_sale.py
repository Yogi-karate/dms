# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

from werkzeug.urls import url_encode


class DmsSaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
    ], string='Finance Type', store=True, default='in')
    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    payment_date = fields.Datetime('Payment Date')
    delivery_date = fields.Datetime('Delivery Date')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('booked', 'Booked'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
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
    product_name = fields.Char('Model', compute='_calculate_product')
    product_variant = fields.Char('Variant', compute='_calculate_product')
    product_color = fields.Char('Color', compute='_calculate_product')
    balance_amount = fields.Float('Balance Amount', compute='_calculate_residual_amount')

    def _calculate_residual_amount(self):
        for order in self:
            balance = 0
            for invoice in order.invoice_ids:
                balance += invoice.residual
            order.balance_amount = balance

    def _calculate_product(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'draft' or pick.state == 'confirmed' or pick.state == 'waiting':
                    order.stock_status = 'not-allotted'
                else:
                    order.stock_status = 'allotted'
                first_order_line = order.order_line[0]
                if first_order_line:
                    order.product_name = first_order_line.product_id.name
                    order.product_variant = first_order_line.product_id.variant_value
                    order.product_color = first_order_line.product_id.color_value

    def write(self, values):
        self.ensure_one()
        location_name = self.team_id.location_id.name
        if location_name and 'state' in values and values['state'] == 'booked':
            if 'Tirumalgiri' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.tir') or _('New')
            if 'Mettuguda' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.met') or _('New')
            if 'Ranigunj' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.rani') or _('New')
            if 'Nacharam' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.nac') or _('New')
        return super(DmsSaleOrder, self).write(values)

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

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            print(line.qty_invoiced, ">>>>>>>>>>>>>>>>>>>>>>>>>>>>", line.name,line.product_uom_qty)
            if line.is_downpayment and line.qty_invoiced == 0.0:
                line.qty_invoiced = 1
            if line.order_id.state in ['sale', 'booked', 'done']:
                if line.product_id.invoice_policy == 'order':
                    print("Product uom qty in invoice qty -----", line.name,line.product_uom_qty, line.qty_invoiced)
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('price_unit', 'discount_price')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit - line.discount_price


class SaleCleanup(models.TransientModel):
    _name = 'dms.order.cleanup'
    name = fields.Char('Customer Name')
    mobile = fields.Char('Customer Mobile')
    order_no = fields.Char('Order No')
    state = fields.Selection([
        ('draft', 'New'),
        ('duplicate', 'Duplicate'),
        ('cancel', 'Cancelled'),
        ('no_order', 'No Order'),
        ('complete', 'Complete'),
    ], string='Status', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    @api.multi
    def reassign_partner(self):
        _logger.info("The number of records to process =>" + str(len(self)))
        for customer in self:
            order = self.env['sale.order'].search([('name', '=', customer.order_no)], limit=1)
            partner = self.env['res.partner'].search(
                [('name', 'ilike', customer.name), ('mobile', '=', customer.mobile)])
            if partner and len(partner) > 1:
                _logger.info("Duplicate customer in System : %s", customer)
                customer.write({'state': 'duplicate'})
                continue
            if not order:
                _logger.info("No such Order to reassign : %s", customer)
                customer.write({'state': 'no_order'})
                continue
            if not partner:
                _logger.info("No such customer to reassign : %s", customer)
                customer.write({'state': 'cancel'})
                continue
            order.write({'partner_id': partner.id})
            vehicle = self.env['vehicle'].search([('order_id', '=', order.id)])
            if not vehicle:
                _logger.info("No such vehicle : %s", order)
                continue
            vehicle.write({'partner_id': partner.id})
            vehicle_leads = self.env['dms.vehicle.lead'].search([('vehicle_id', '=', vehicle.id)])
            for lead in vehicle_leads:
                lead.write({
                    'name': vehicle.partner_name + '-' + vehicle.product_id.name,
                    'partner_name': vehicle.partner_name,
                    'mobile': vehicle.partner_mobile
                })
            customer.write({'state': 'complete'})

    @api.model
    def order_clean_up(self):
        _logger.info("---------Order cleanup process started ---------")
        self.env['dms.order.cleanup'].search([('state', '=', 'draft')]).reassign_partner()
        _logger.info("---------Order cleanup process completed ---------")
