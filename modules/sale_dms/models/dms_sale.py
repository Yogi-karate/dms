# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

from werkzeug.urls import url_encode


class DmsSaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'


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
