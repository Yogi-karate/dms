# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class Vehicle(models.Model):
    _name = 'vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle'
    name = fields.Char(
        'Engine Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Vehicle Engine Number")
    _sql_constraints = [
        ('name_ref_uniq', 'unique (name, product_id)', 'The combination of serial number and product must be unique !'),
    ]
    ref = fields.Char('Internal Reference',
                      help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    state = fields.Selection([
        ('transit', 'In-Transit'),
        ('in-stock', 'Physical Stock'),
        ('waiting', 'Waiting'),
        ('reserved', 'Allocated'),
        ('sold', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, compute='_get_vehicle_state', copy=False, index=True,
        track_visibility='onchange', track_sequence=3,
        default='transit',store=True)
    chassis_no = fields.Char('Chassis Number', help="Unique Chasis number of the vehicle")
    registration_no = fields.Char('Registration Number', help="Unique Registration number of the vehicle")
    lot_id = fields.Many2one('stock.production.lot', string='Vehicle Serial Number',
                             change_default=True, ondelete='cascade')
    battery_no = fields.Char('Battery Number', help="Unique Battery number of the vehicle")
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], required=True)
    model = fields.Char('Model', readonly=True, compute='_get_product_details')
    variant = fields.Char('Variant', readonly=True, compute='_get_product_details')
    color = fields.Char('Color', readonly=True, compute='_get_product_details')
    model_year = fields.Char('Manufatured Year', readonly=True)
    invoice_date = fields.Date('Invoice Date')
    vehicle_age = fields.Integer('Age', readonly=True, compute='_get_vehicle_age')
    location_id = location_id = fields.Many2one(
        'stock.location', 'Location', compute='_get_location_details')
    partner_name = fields.Char('Customer', compute='_get_customer_details', store=True)
    partner_mobile = fields.Char('Mobile No.', compute='_get_customer_details', store=True)
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
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('dms.enquiry'))
    insurance_history = fields.One2many('vehicle.insurance', 'vehicle_id', string='Vehicle Insurance', copy=True,
                                        auto_join=True)
    finance = fields.Many2one('vehicle.finance', string='Vehicle Finance', change_default=True, ondelete='cascade')

    @api.depends('lot_id.quant_ids')
    def _change_state(self):
        for vehicle in self:
            vehicle.state = "reserved"
    @api.depends('order_id')
    def _on_change_sale_order(self):
        self.partner_id = self.order_id.partner_id
        # We only care for the customer if sale order is entered.
        self.date_order = self.order_id.date_order

    @api.model_create_multi
    def create(self, vals_list):
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

    @api.depends('partner_id')
    @api.multi
    def _get_customer_details(self):
        for vehicle in self:
            vehicle.partner_name = vehicle.partner_id.name
            vehicle.partner_mobile = vehicle.partner_id.mobile
            vehicle.partner_email = vehicle.partner_id.email
            vehicle.address = vehicle.partner_id.street

    @api.multi
    def _get_vehicle_details(self):
        for vehicle in self:
            vehicle.fuel_type = vehicle.product_id.fuel_type

    @api.multi
    def _get_product_details(self):
        for vehicle in self:
            if vehicle.product_id:
                vehicle.model = vehicle.product_id.product_tmpl_id.name
                vehicle.variant = vehicle.product_id.variant_value
                vehicle.color = vehicle.product_id.color_value

    @api.multi
    def _get_vehicle_state(self):
        for vehicle in self:
            vehicle.state = 'transit'

    @api.multi
    def _get_location_details(self):
        for vehicle in self:
            quant = self.sudo().env['stock.quant'].search([('lot_id','=',vehicle.lot_id.id)])
            # quant = vehicle.lot_id.quant_id
            if quant:
                vehicle.location_id = quant.location_id
                vehicle.state = 'in-stock'
            else:
                vehicle.location_id = self.env['stock.location'].search([('id', '=', 1)])

    @api.multi
    def _get_vehicle_age(self):
        today = fields.Datetime.now()
        for vehicle in self:
            vehicle.vehicle_age = (today - vehicle.date_order).days


class VehicleInsurance(models.Model):
    _name = 'vehicle.insurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle Insurance Details'

    policy_date = fields.Date('Policy Due Date')
    insurance_company = fields.Many2one('res.insurance.company')
    policy_number = fields.Char('Policy Number')
    policy_idv = fields.Char('IDV value')
    vehicle_id = fields.Many2one('vehicle', string='Engine No.', required=True, ondelete='cascade', index=True,
                                 copy=False)


class VehicleFinance(models.Model):
    _name = 'vehicle.finance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle Finance Details'

    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    finance_amount = fields.Float('Amount', digits=dp.get_precision('Product Price'), default=0.0)
    finance_agreement_date = date_order = fields.Datetime(string='Finance Agreement Date', default=fields.Datetime.now)
    loan_tenure = fields.Char('Tenure', help="Loan Tenure")
    loan_amount = fields.Float('Loan Amount', digits=dp.get_precision('Product Price'), default=0.0)
    loan_approved_amount = fields.Float('Approved Amount', digits=dp.get_precision('Product Price'), default=0.0)
    loan_rate = fields.Float("Rate of Interest", digits=(2, 2), help='The rate of interest for loan')
    loan_emi = fields.Float('EMI', digits=dp.get_precision('Product Price'), default=0.0)
    loan_commission = fields.Float('Commission ', digits=dp.get_precision('Product Price'), default=0.0)
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
    ], string='Finance Type', store=True, default='in')
