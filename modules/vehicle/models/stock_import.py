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
    order_no = fields.Char('Order No')

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
            }
            self.env['vehicle'].create(vals)
            vehicle.status = True

    @api.model
    def _create_inventory_adjustment(self):
        adj_vals = {"state": "confirm",
                    "location_id": 12, "filter": "partial",
                    "date": "2019-11-07 19:33:42", "company_id": 1,
                    "name": "Y Service",
                    "accounting_date": false,
                    "product_id": false,
                    "category_id": false, "lot_id": false,
                    "partner_id": false, "package_id": false, "exhausted": false,
                    "line_ids": [[0, "virtual_535", {"product_id": 2011, "location_id": 12, "prod_lot_id": 63192,
                                                     "package_id": false, "partner_id": false, "product_qty": 1,
                                                     "product_tracking": "serial", "product_uom_id": 1,
                                                     "product_uom_category_id": 1, "theoretical_qty": 0,
                                                     "state": "confirm"}]],
                    "move_ids": [], "id": 1},
        "line_ids", {"state": "1", "name": "", "location_id": "1", "filter": "1", "date": "", "accounting_date": "",
                     "company_id": "", "product_id": "", "category_id": "", "lot_id": "", "partner_id": "",
                     "package_id": "", "exhausted": "", "line_ids": "1", "line_ids.product_tracking": "",
                     "line_ids.product_id": "1", "line_ids.product_uom_id": "1",
                     "line_ids.product_uom_category_id": "", "line_ids.location_id": "1", "line_ids.prod_lot_id": "1",
                     "line_ids.package_id": "1", "line_ids.partner_id": "1",
                     "line_ids.theoretical_qty": "", "line_ids.product_qty": "", "line_ids.state": "", "move_ids": "",
                     "move_ids.product_id": "1", "move_ids.picking_id": "", "move_ids.create_date": "",
                     "move_ids.date_expected": "1", "move_ids.scrapped": "", "move_ids.state": "",
                     "move_ids.location_id": "", "move_ids.location_dest_id": "1", "move_ids.quantity_done": "",
                     "move_ids.product_uom": "1"},
