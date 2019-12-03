# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class Vehicle(models.Model):
    _name = 'vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle'
    name = fields.Char(
        'Chassis Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Vehicle Chassis Number")
    _sql_constraints = [
        ('name_ref_uniq', 'unique (name, product_id)', 'The combination of serial number and product must be unique !'),
    ]
    ref = fields.Char('Internal Reference',
                      help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    state = fields.Selection([
        ('waiting', 'Pending'),
        ('transit', 'In-Transit'),
        ('in-stock', 'Physical Stock'),
        ('sold', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True,
        track_visibility='onchange', track_sequence=3, compute='_get_vehicle_state', store=True)
    engine_no = fields.Char('Engine Number', help="Unique Engine number of the vehicle")
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
    age = fields.Integer('Age', readonly=True, compute='_get_vehicle_age')
    location_id = fields.Many2one(
        'stock.location', 'Location', compute='_get_location_details', store=True)
    partner_name = fields.Char('Customer', compute='_get_customer_details', store=True)
    partner_mobile = fields.Char('Mobile No.', compute='_get_customer_details', store=True)
    partner_email = fields.Char('Email', compute='_get_customer_details')
    date_order = fields.Datetime('Sale-Date')
    address = fields.Char('Address', compute='_get_customer_details')
    fuel_type = fields.Char('Fuel Type', compute='_get_vehicle_details')
    partner_id = fields.Many2one('res.partner', compute='_get_customer_details', store=True)
    order_id = fields.Many2one('sale.order')
    purchase_id = fields.Many2one('purchase.order')
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
    allocation_state = fields.Selection([
        ('free', 'Free'),
        ('allocated', 'Allocated'),
    ], string='Allocation', readonly=True, copy=False, index=True,
        track_visibility='onchange', track_sequence=3,
        default='free', store=True)
    allocation_date = fields.Date('Allocation Date')
    delivery_date = fields.Date('Delivery Date')
    allocation_age = fields.Integer('Allocation Age', readonly=True, compute='_get_vehicle_allocation_age')
    order_count = fields.Integer(string='Order Count', compute='_get_sale_order_count', readonly=True)
    purchase_count = fields.Integer(string='Purchase Count', compute='_get_purchase_order_count', readonly=True)
    delivery_count = fields.Integer(string='Delivery Count', compute='_get_sale_order_count', readonly=True)
    receipt_count = fields.Integer(string='Receipt Count', compute='_get_purchase_order_count', readonly=True)

    @api.multi
    def _get_sale_order_count(self):
        for vehicle in self:
            if vehicle.order_id:
                vehicle.order_count = 1
                vehicle.delivery_count = 1
            else:
                vehicle.order_count = 0
                vehicle.delivery_count = 0

    @api.multi
    def _get_purchase_order_count(self):
        for vehicle in self:
            if vehicle.purchase_id:
                vehicle.purchase_count = 1
                vehicle.receipt_count = 1
            else:
                vehicle.purchase_count = 0
                vehicle.receipt_count = 0

    @api.multi
    def change_vehicle_state(self):
        for vehicle in self:
            print("-------In vehicle change location compute-------")
            if vehicle.state != 'sold':
                quant = vehicle.lot_id.quant_ids.filtered(lambda l: l.quantity == 1)
                if quant:
                    vehicle.location_id = quant.location_id
            else:
                vehicle.location_id = False

    @api.depends('lot_id.quant_ids.location_id', 'lot_id.quant_ids.quantity')
    @api.multi
    def _get_vehicle_state(self):
        for vehicle in self:
            print("!!!!!!!state change for vehicle !!!!!!!!!")
            state = vehicle.state
            quant = vehicle.lot_id.quant_ids.filtered(lambda l: l.quantity == 1)
            print("the quant in state compute", quant)
            if quant:
                location_id = quant.location_id
                if location_id and location_id.usage == 'transit':
                    state = 'transit'
                else:
                    if location_id and location_id.usage == 'internal':
                        state = 'in-stock'
                    else:
                        if vehicle.state != 'waiting':
                            state = 'waiting'
                if vehicle.state != state:
                    vehicle.state = state
            else:
                vehicle.state = 'waiting'

    @api.depends('lot_id.quant_ids.location_id', 'lot_id.quant_ids.quantity')
    @api.multi
    def _get_location_details(self):
        for vehicle in self:
            vehicle.change_vehicle_state()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'no_lot' not in vals:
                self._create_vehicle_lot(vals)
        return super(Vehicle, self).create(vals_list)

    def _create_vehicle_lot(self, vals):
        new_lot = self.env['stock.production.lot'].create({
            'name': vals['name'],
            'product_id': vals['product_id'],
        })
        vals['lot_id'] = new_lot.id
        print("The new Lot created is " + new_lot.name)

    @api.depends('order_id')
    @api.multi
    def _get_customer_details(self):
        for vehicle in self:
            vehicle.partner_id = vehicle.order_id.partner_id
            vehicle.date_order = vehicle.order_id.date_order
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
    def _get_vehicle_allocation_age(self):
        today = fields.Date.today()
        for vehicle in self:
            if not vehicle.allocation_date:
                vehicle.allocation_age = 0
            else:
                vehicle.allocation_age = (today - vehicle.allocation_date).days

    @api.multi
    def _get_vehicle_age(self):
        today = fields.Date.today()
        for vehicle in self:
            if not vehicle.invoice_date:
                vehicle.age = 0
            else:
                vehicle.age = (today - vehicle.invoice_date).days
    @api.multi
    def action_view_sale_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        print(action)
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['res_id'] = self.order_id.id
        return action

    @api.multi
    def action_view_purchase_order(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        print(action)
        action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['res_id'] = self.purchase_id.id
        return action

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.order_id.picking_ids
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def action_view_receipt(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.purchase_id.picking_ids
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def action_view_transfers(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.order_id.picking_ids
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action


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
