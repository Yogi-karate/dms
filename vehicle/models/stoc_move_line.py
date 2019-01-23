# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import Counter

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools.pycompat import izip
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = "stock.move.line"

    vehicle_id = fields.Many2one('vehicle', help='Move line Associated to a specific vehicle')

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            print(vals)
            # If the move line is directly create on the picking view.
            # Created vehicles lot id is associated to this move line
            if 'vehicle_id' in vals :
                vals['lot_id'] = self._create_vehicle_lot(vals)
        return super(StockMoveLine, self).create(vals_list)

    def _create_vehicle_lot(self,vals):
        vehicle = self.env['vehicle'].browse(vals['vehicle_id'])
        lot = vehicle.lot_id
        if lot:
            return lot.id
        if 'product_id' in vals and vals['product_id']:
            product = self.env['product.product'].browse(vals['product_id'])
        else:
            product = self.product_id
        new_lot = self.env['stock.production.lot'].create({
            'name': vehicle.name,
            'product_id': product.id,
        })
        print("The new Lot created is " + new_lot.name)
        return new_lot.id

    def _update_vehicle_lot(self,vals):
        vehicle = self.env['vehicle'].browse(vals['vehicle_id'])
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
        if 'vehicle_id' in vals:
            self._update_vehicle_lot(vals)
        return super(StockMoveLine, self).write(vals)