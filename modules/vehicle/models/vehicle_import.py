import logging
from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


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

    @api.model
    def create_vehicles(self):
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")
        self._create_vehicles()
        self.env['dms.vehicle.import'].search([('status', '=', True)]).unlink()
        _logger.info("!!!!!!!!!!!!!!End of ->  Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")

    @api.model
    def _create_vehicles(self):
        od_vehicles = self.env['dms.vehicle.import'].search([], limit=1000)
        _logger.info("The number of records to process =>", str(len(od_vehicles)))
        count = 0
        for vehicle in od_vehicles:
            count = count + 1
            self = self.sudo()
            product = self.env['product.product'].search(
                [('name', 'ilike', vehicle.model), ('fuel_type', 'ilike', vehicle.fuel_type)], limit=1)
            if not product or not vehicle.vin_no or not vehicle.customer_name or not vehicle.date_of_sale:
                print("Cannot process vehicle -> ", vehicle.vin_no, vehicle.customer.name, count)
                continue
            print("In Vehicle loop of import ^^^^^^^^", vehicle.customer_name, vehicle.vin_no, vehicle.date_of_sale,
                  product)
            _logger.info("-----------Starting creation of partner and vehicle------------")
            partner = self.env['res.partner'].create(vehicle.create_partner(vehicle))
            vals = {
                'name': vehicle.vin_no,
                'chassis_no': vehicle.chassis_no,
                'registration_no': vehicle.reg_no,
                'date_order': vehicle.date_of_sale,
                'dealer_name': vehicle.dealer,
                'partner_id': partner.id,
                'product_id': product.id,
                'source': 'od',
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
