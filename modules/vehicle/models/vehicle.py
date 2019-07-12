# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime

from odoo.addons import decimal_precision as dp


class Vehicle(models.Model):
    _name = 'vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle'
    name = fields.Char(
        'Engine Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Machine Number")
    _sql_constraints = [
        ('name_ref_uniq', 'unique (name, product_id)', 'The combination of serial number and product must be unique !'),
    ]
    ref = fields.Char('Internal Reference',
                      help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    state = fields.Selection([
        ('transit', 'Purchased'),
        ('in-stock', 'Showroom'),
        ('sold', 'Allocated'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='transit')
    chassis_no = fields.Char('Chasis Number', help="Unique Chasis number of the vehicle")
    registration_no = fields.Char('Registration Number', help="Unique Registration number of the vehicle")
    lot_id = fields.Many2one('stock.production.lot', string='Vehicle Serial Number',
                             change_default=True, ondelete='cascade')
    battery_no = fields.Char('Battery Number', help="Unique Battery number of the vehicle")
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], required=True)
    color = fields.Char('Color', readonly=True, compute='_get_color')
    partner_name = fields.Char('Customer', compute='_get_customer_details')
    partner_mobile = fields.Char('Mobile No.', compute='_get_customer_details')
    partner_email = fields.Char('Email', compute='_get_customer_details')
    date_order = fields.Datetime('Sale-Date')
    address = fields.Char('Address', compute='_get_customer_details')
    fuel_type = fields.Char('Fuel Type', compute='_get_vehicle_details')
    partner_id = fields.Many2one('res.partner')
    order_id = fields.Many2one('sale.order')
    source = fields.Selection([
        ('od', 'Other Dealer'),
        ('saboo', 'Saboo'),
    ], string='Source', store=True, default='saboo')
    dealer_name = fields.Char('Dealer', default='saboo')

    @api.depends('order_id')
    def _on_change_sale_order(self):
        self.partner_id = self.order_id.partner_id
        # We only care for the customer if sale order is entered.
        self.date_order = self.order_id.date_order

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            #if not vals['no_lot']:
                self._create_vehicle_lot(vals)
        return super(Vehicle, self).create(vals_list)

    def _create_vehicle_lot(self, vals):
        new_lot = self.env['stock.production.lot'].create({
            'name': vals['name'],
            'product_id': vals['product_id'],
        })
        vals['lot_id'] = new_lot.id
        print("The new Lot created is " + new_lot.name)

    @api.multi
    def write(self, vals):
        return super(Vehicle, self).write(vals)

    @api.one
    def _get_vehicle_details(self):
        self.fuel_type = self.product_id.fuel_type

    @api.multi
    def _get_customer_details(self):
        for vehicle in self:
            vehicle.partner_name = vehicle.partner_id.name
            vehicle.partner_mobile = vehicle.partner_id.mobile
            vehicle.partner_email = vehicle.partner_id.email
            vehicle.address = vehicle.partner_id.street

    @api.one
    def _get_vehicle_details(self):
        self.fuel_type = self.product_id.fuel_type

    @api.one
    def _get_color(self):
        # We only care for the customer if sale order is entered.
        if self.product_id:
            color = self.product_id.display_name
        print("The color is - " + color)
        return "BLACK"

    @api.multi
    def action_in_stock(self):
        return self.write({'state': 'in-stock'})
