# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

from odoo.addons import decimal_precision as dp

class Vehicle(models.Model):
    _name = 'vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle'
    name = fields.Char(
        'Vehicle Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Machine Number")
    ref = fields.Char('Internal Reference',
                      help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    state = fields.Selection([
        ('transit', 'Purchased'),
        ('in-stock', 'Showroom'),
        ('sold', 'Allocated'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='transit')
    chassis_no = fields.Char('Chasis Number',help = "Unique Chasis number of the vehicle")
    registration_no = fields.Char('Registration Number', help="Unique Registration number of the vehicle")
    lot_id = fields.Many2one('stock.production.lot', string='Vehicle Serial Number',
                                 change_default=True, ondelete='restrict')
    battery_no = fields.Char('Battery Number',help = "Unique Battery number of the vehicle")
    #customer_id = fields.Many2one('res.partner', string='Customer', readonly=True, compute='_get_customer')
    financier_name = fields.Many2one('res.bank', string = 'Financier', help="Bank for finance")
    finance_amount = fields.Float('Amount',digits=dp.get_precision('Product Price'), default=0.0)
    finance_agreement_date = date_order = fields.Datetime(string='Finance Agreement Date', default=fields.Datetime.now)
    loan_tenure = fields.Char('Tenure', help="Loan Tenure")
    loan_amount = fields.Float('Loan Amount',digits=dp.get_precision('Product Price'), default=0.0)
    loan_approved_amount = fields.Float('Approved Amount',digits=dp.get_precision('Product Price'), default=0.0)
    loan_rate = fields.Float("Rate of Interest", digits=(2, 2), help='The rate of interest for loan')
    loan_emi = fields.Float('EMI',digits=dp.get_precision('Product Price'), default=0.0)
    loan_commission = fields.Float('Commission ', digits=dp.get_precision('Product Price'), default=0.0)
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
    ], string='Finance Type', store=True, default='out')
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], required=True)
    color = fields.Char('Color', readonly=True, compute='_get_color')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            print(vals)
        return super(Vehicle, self).create(vals_list)

    @api.multi
    def write(self, vals):
        return super(Vehicle, self).write(vals)

    @api.one
    def _get_customer(self):
        # We only care for the customer if sale order is entered.
        if self.order_id:
            customer_id = self.order_id.partner_id
            self.customer_id = customer_id

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