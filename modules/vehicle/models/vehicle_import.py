import logging
from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class ODVehicle(models.Model):
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
    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    @api.model
    def create_vehicles(self):
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")
        self._create_vehicles()
        self.env['dms.vehicle.import'].search([('status', '=', True)]).unlink()
        _logger.info("!!!!!!!!!!!!!!End of ->  Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")

    @api.model
    def _create_vehicles(self):
        od_vehicles = self.env['dms.vehicle.import'].search([])
        _logger.info("The number of records to process =>" + str(len(od_vehicles)))
        count = 0
        for vehicle in od_vehicles:
            count = count + 1
            self = self.sudo()
            if not vehicle.model:
                print("no model",vehicle.model)
                continue
            name = vehicle.model.strip()
            fuel = vehicle.fuel_type.strip()
            pro = self.env['product.product'].search([('name', 'ilike',name)], limit=1)
            print(pro,"length of------------------------ ",vehicle.model,"---is---",len(vehicle.model))
            product = self.env['product.product'].search([('name', 'ilike', name), ('fuel_type', 'ilike', fuel)], limit=1)
            if not product:
                print("not product")
                print(vehicle.model,"--------------------------------",vehicle.fuel_type)
                print(vehicle.model)
            if not product or not vehicle.vin_no or not vehicle.customer_name or not vehicle.date_of_sale:
                print("Cannot process vehicle -> ", count)
                print(product)
                print(vehicle.vin_no)
                print(vehicle.customer_name)
                print(vehicle.date_of_sale)
                print("--------------------------------------------------------------------------")
                vehicle.state = 'cancel'
                continue
            duplicate = self.env['vehicle'].search(['|',('name','=',vehicle.vin_no),('chassis_no','=',vehicle.vin_no)])
            if duplicate:
                print("Cannot process duplicate vehicle -> ", count)
                vehicle.state = 'cancel'
                continue

            _logger.info("-----------Starting creation of partner and vehicle------------")
            Partner = self.env['res.partner']
            partner = Partner.search([('name', 'ilike', '%' + vehicle.customer_name + '%'),
                                      ('mobile', 'ilike', '%' + vehicle.mobile + '%')], limit=1)
            if not partner:
                partner = self.env['res.partner'].create(vehicle.create_partner(vehicle))
            source = ''
            if not self.dealer == 'saboo':
                    source = 'saboo'
            else:
                    source = 'od'
            vals = {
                'name': vehicle.vin_no,
                'chassis_no': vehicle.chassis_no,
                'registration_no': vehicle.reg_no,
                'date_order': vehicle.date_of_sale,
                'dealer_name': vehicle.dealer,
                'partner_id': partner.id,
                'product_id': product.id,
                'source': source,
                'no_lot': True
            }
            self.env['vehicle'].create(vals)
            vehicle.status = True

    @api.model
    def update_vehicle_from_ref(self):
        vehicles = self.env['vehicle'].search([('ref', '!=', False)])
        for vehicle in vehicles:
            order_id = self.env['sale.order'].search([('name', '=', vehicle.ref)])
            if order_id:
                vehicle.order_id = order_id
                vehicle.partner_id = order_id.partner_id
                vehicle.date_order = order_id.date_order

    def create_partner(self, vehicle):
        return {
            'name': vehicle.customer_name,
            'mobile': vehicle.mobile,
            'street': vehicle.address,
            'customer': True}
