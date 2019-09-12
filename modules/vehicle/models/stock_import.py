import logging
from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class StockImport(models.Model):
    _name = 'dms.stock.import'

    hyundai_invoice_no = fields.Char('HMI Invoice')
    import_date = fields.Char('Import Date')
    model = fields.Char('model')
    variant = fields.Char('variant')
    color = fields.Char('color')
    color_code = fields.Char('color code')
    engine_no = fields.Char('Engine Number')
    status = fields.Char('Status')
    location = fields.Char('Vehicle Location')
    remarks = fields.Char('Remarks')
    gdms_bill_date = fields.Char('Hyundai Billed Date')
    vin_no = fields.Char('Chassis Number')
    reg_no = fields.Char('Registration Number')
    status = fields.Boolean('status')

    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    ignore_reason = fields.Char('Reason for Cancel')

    @api.model
    def create_vehicles(self):
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")
        self._create_vehicles()
        self.env['dms.vehicle.import'].search([('status', '=', True)]).unlink()
        _logger.info("!!!!!!!!!!!!!!End of ->  Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")

    @api.model
    def _create_vehicles(self):
        od_vehicles = self.env['dms.stock.import'].search([], limit=10000)
        _logger.info("The number of records to process =>" + str(len(od_vehicles)))
        count = 0

        ignore_reason = ''
        for vehicle in od_vehicles:
            print("oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo----------", count)
            count = count + 1
            self = self.sudo()
            if not vehicle.model:
                print("no model", vehicle.model)
                ignore_reason = 'Vehicle Model not present'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            if not vehicle.variant:
                print("no Variant", vehicle)
                ignore_reason = 'Vehicle Variant' \
                                ' Type not present'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            if not vehicle.color:
                print("no Color", vehicle)
                ignore_reason = 'Vehicle Color' \
                                ' Type not present'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue

            name = vehicle.model.strip().lower()
            variant = vehicle.variant.strip().lower()
            color = vehicle.color.strip().lower()
            # pro = self.env['product.product'].search([('name', 'ilike',vehicle.model)], limit=1)
            # print(pro,"length of------------------------ ",vehicle.model,"---is---",len(vehicle.model))
            product = self.env['product.product'].search([('name', 'ilike', name), ('variant_value', 'ilike', variant), ('color_value', 'ilike', color)],
                                                     limit=1)
            print(product)
            print(color,"---",variant,"-----",name)
            if not product:
                ignore_reason = 'Product not present'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            if not vehicle.vin_no:
                ignore_reason = 'Vin is null'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            # if not vehicle.customer_name :
            #     ignore_reason = 'NO Customer details'
            #     vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
            #     continue

            duplicate = self.env['vehicle'].search(
                ['|', ('name', '=', vehicle.vin_no), ('chassis_no', '=', vehicle.vin_no)])
            if duplicate:
                print(
                    "Cannot process duplicate vehicle------------------------------------------------------------------------------------ -> ",
                    count)
                ignore_reason = 'Duplicate Vehicle'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue

            _logger.info("-----------Starting creation of partner and vehicle------------")
            # Partner = self.env['res.partner']
            # partner = Partner.search([('name', 'ilike', '%' + vehicle.customer_name + '%'),
            #                           ('mobile', 'ilike', '%' + vehicle.mobile + '%')], limit=1)
            # if not partner:
            #     partner = self.env['res.partner'].create(vehicle.create_partner(vehicle))
            # source = ''
            # if not vehicle.dealer:
            #     source = 'od'
            # elif 'saboo' in vehicle.dealer.lower():
            #     source = 'saboo'
            # else:
            #     source = 'od'
            vals = {
                'name': vehicle.engine_no,
                'chassis_no': vehicle.vin_no,
                'registration_no': vehicle.reg_no,
                'product_id': product.id,
                'source': 'saboo',

            }
            self.env['vehicle'].create(vals)
            vehicle.status = True

    # @api.model
    # def update_vehicle_from_ref(self):
    #     vehicles = self.env['vehicle'].search([('ref', '!=', False)])
    #     for vehicle in vehicles:
    #         order_id = self.env['sale.order'].search([('name', '=', vehicle.ref)])
    #         if order_id:
    #             vehicle.order_id = order_id
    #             vehicle.partner_id = order_id.partner_id
    #             vehicle.date_order = order_id.date_order
    #
    # def create_partner(self, vehicle):
    #     return {
    #         'name': vehicle.customer_name,
    #         'mobile': vehicle.mobile,
    #         'street': vehicle.address,
    #         'customer': True}
