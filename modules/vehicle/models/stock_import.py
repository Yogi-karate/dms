import logging
from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class StockImport(models.Model):
    _name = 'dms.stock.import'

    invoice_date = fields.Date('Vehicle Purchase Date')
    import_date = fields.Date('Import Date', default=fields.Date.today)
    model = fields.Char('model')
    variant = fields.Char('variant')
    color = fields.Char('color')
    engine_no = fields.Char('Engine Number')
    status = fields.Char('Status')
    location = fields.Char('Vehicle Location')
    remarks = fields.Char('Remarks')
    vin_no = fields.Char('Chassis Number')
    reg_no = fields.Char('Registration Number')
    status = fields.Boolean('status')
    order_no = fields.Char('Order No')
    model_year = fields.Char('Manufatured Year')
    inventoried_location = fields.Many2one('stock.location', 'inventoried_location')
    inventory_location = fields.Many2one('stock.location', 'inventory_location')
    product_id = fields.Many2one('product.product', 'product')

    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Failed'),
    ], string='Status', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    ignore_reason = fields.Char('Failure Reason')

    @api.model
    def create_vehicles(self):
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")
        self._create_vehicles()
        self.env['dms.stock.import'].search([('status', '=', True)]).unlink()
        _logger.info("!!!!!!!!!!!!!!End of ->  Creation of Vehicle from Import Data!!!!!!!!!!!!!!!!")

    @api.model
    def _create_vehicles(self):
        od_vehicles = self.env['dms.stock.import'].search([('state', '=', 'draft')], limit=1000)
        _logger.info("The number of records to process =>" + str(len(od_vehicles)))
        count = 0

        ignore_reason = ''
        for vehicle in od_vehicles:
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

            name = vehicle.model.strip()
            variant = vehicle.variant.strip()
            color = vehicle.color.strip()
            product = self.env['product.product'].search(
                [('name', '=', name), ('variant_value', '=', variant), ('color_value', '=', color)])
            print(product)
            print(color, "---", variant, "-----", name)
            if len(product) > 1:
                ignore_reason = 'More than one product matched'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            if not product:
                ignore_reason = 'Product not present'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            if not vehicle.engine_no:
                ignore_reason = 'Engine number is null'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            if not vehicle.vin_no:
                ignore_reason = 'Vin is null'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            self.product_id = product
            duplicate = self.env['vehicle'].search(
                ['|', ('name', '=', vehicle.vin_no), ('chassis_no', '=', vehicle.vin_no)])
            if duplicate:
                ignore_reason = 'Duplicate Vehicle'
                vehicle.write({'ignore_reason': ignore_reason, 'state': 'cancel'})
                continue
            _logger.info("-----------Starting creation of partner and vehicle------------")
            vals = {
                'name': vehicle.engine_no,
                'chassis_no': vehicle.vin_no,
                'registration_no': vehicle.reg_no,
                'product_id': product.id,
                'source': 'saboo',
                'ref': vehicle.order_no,
                'model_year': vehicle.model_year,
                'invoice_date': vehicle.invoice_date,
            }
            self.env['vehicle'].create(vals)
            vehicle.status = True
