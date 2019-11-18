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
    lot_id = fields.Many2one('stock.production.lot', 'Vehicle Number')
    vehicle_id = fields.Many2one('vehicle', help='Move line Associated to a specific vehicle')
    # allocated_qty = fields.Float(
    #     'Real Allocated Quantity', digits=0,
    #     compute='_compute_product_qty', inverse='_set_product_qty', store=True)

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            print(vals)
            # If the move line is directly created on the picking view.
            # vehicles lot id is associated to this move line
            if 'vehicle_id' in vals:
                self._update_vehicle_lot(vals)
                print("The updated vals in create is ", vals)
        return super(StockMoveLine, self).create(vals_list)

    def write(self, vals):
        """ Through the interface, we allow users to change the charateristics of a move line. If a
        quantity has been reserved for this move line, we impact the reservation directly to free
        the old quants and allocate the new ones.
        """
        print(vals)
        print(self)
        if 'vehicle_id' in vals:
            self._update_vehicle_lot(vals)
            print("The updated vals in create is ", vals)
        return super(StockMoveLine, self).write(vals)

    def _update_vehicle_lot(self, vals):
        vehicle = self.env['vehicle'].browse(vals['vehicle_id'])
        lot = vehicle.lot_id
        vals.update({'lot_id': vehicle.lot_id.id, 'lot_name': vehicle.name})
        print("The updated Lot is " + str(lot))
        # return vals
