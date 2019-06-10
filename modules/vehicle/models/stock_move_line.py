# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _



class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = "stock.move.line"

    vehicle_id_receipt = fields.Many2one('vehicle', string='Vehicle', help='Move line Associated to a specific vehicle')
    vehicle_id_delivery = fields.Many2one('vehicle', string='Vehicle', help='Move line delivery Associated to a specific vehicle')

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            print(vals)
            # If the move line is directly create on the picking view.
            # Created vehicles lot id is associated to this move line
            if 'vehicle_id_receipt' in vals :
                vehicle = self.env['vehicle'].browse(vals['vehicle_id_receipt'])
                vals['lot_id'] = vehicle.lot_id.id
            if 'vehicle_id_delivery' in vals:
                vehicle = self.env['vehicle'].browse(vals['vehicle_id_delivery'])
                vals['lot_id'] = vehicle.lot_id.id
        return super(StockMoveLine, self).create(vals_list)



    def _update_vehicle_lot(self,vals):
        # vehicle = self.env['vehicle'].browse(vals['vehicle_id'])
        # lot = vehicle.lot_id
        if 'vehicle_id_receipt' in vals:
            vehicle = self.env['vehicle'].browse(vals['vehicle_id_receipt'])
            lot = vehicle.lot_id
        if 'vehicle_id_delivery' in vals:
            vehicle = self.env['vehicle'].browse(vals['vehicle_id_delivery'])
            lot = vehicle.lot_id
        if not lot:
            lot = self._create_vehicle_lot(vals)
            vehicle.lot_id = lot
            vehicle.action_in_stock()
        vals['lot_id'] = vehicle.lot_id.id
        print("The updated Lot is " + str(lot))

    def write(self, vals):
        """ Through the interface, we allow users to change the charateristics of a move line. If a
        quantity has been reserved for this move line, we impact the reservation directly to free
        the old quants and allocate the new ones.
        """
        print(vals)
        print(self)
        # if 'vehicle_id' in vals:
        #     vehicle = self.env['vehicle'].browse(vals['vehicle_id'])
        #     vals['lot_id'] = vehicle.lot_id.id

        if 'vehicle_id_receipt' in vals:
            vehicle = self.env['vehicle'].browse(vals['vehicle_id_receipt'])
            vals['lot_id'] = vehicle.lot_id.id
        if 'vehicle_id_delivery' in vals:
            vehicle = self.env['vehicle'].browse(vals['vehicle_id_delivery'])
            vals['lot_id'] = vehicle.lot_id.id
        return super(StockMoveLine, self).write(vals)