from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime


class ODVehicle(models.TransientModel):
    _name = 'dms.vehicle.import'
    vin_no = fields.Char('VIN No')
    reg_no = fields.Char('Reg no')
    date_of_sale = fields.Date('Date of Sale')
    last_service_type = fields.Char('Last Service Type')
    last_service_date = fields.Char('Last Service Date')
    fuel_type = fields.Char('Fuel Type')
    last_service_KM = fields.Char('Last Service KM')
    dealer = fields.Char('Dealer')
    model = fields.Char('MODEL')
    customer_name = fields.Char('Customer Name')
    address = fields.Char('Address')
    mobile = fields.Char('Mobile')
    partner_id = fields.Many2one('res.partner')
    status = fields.Boolean('status')
    chassis_no = fields.Char('Chassis No')

    def create_vehicles(self):
        self._create_vehicles()
        self.env['dms.vehicle.import'].search([('status', '=', True)]).unlink()

    def _create_vehicles(self):
        od_vehicles = self.env['dms.vehicle.import'].search([])
        for vehicle in od_vehicles:
            self = self.sudo()
            product = self.env['product.product'].search(
                [('name', 'ilike', vehicle.model), ('fuel_type', 'ilike', vehicle.fuel_type)], limit=1)
            if not product:
                continue
            partner = self.env['res.partner'].create(vehicle.create_partner(vehicle))
            vals = {
                'name': vehicle.vin_no,
                'chassis_no': vehicle.chassis_no,
                'registration_no': vehicle.reg_no,
                'date_order': vehicle.date_of_sale,
                'dealer_name': vehicle.dealer,
                'partner_id': partner.id,
                'product_id': product.id,
                'no_lot': True
            }
            self.env['vehicle'].create(vals)
            vehicle.status = True

    def update_vehicle_from_ref(self):
        vehicles = self.env['vehicle'].search([('ref', '!=', False)])
        for vehicle in vehicles:
            order_id = self.env['sale.order'].search([('name', '=', vehicle.ref)])
            if order_id:
                vehicle.order_id = order_id
                vehicle.partner_id = order_id.partner_id
                vehicle.date_order = order_id.date_order
        od_vehicles = self.env['vehicle'].search([('ref', '=', False)])
        for vehicle in od_vehicles:
            vehicle.source = 'od'


    def create_partner(self, vehicle):
        return {
            'name': vehicle.customer_name,
            'mobile': vehicle.mobile,
            'street': vehicle.address,
            'customer': True}
