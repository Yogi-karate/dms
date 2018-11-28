# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductionLot(models.Model):
    _name = 'vehicle'
    _inherit = 'stock.production.lot'
    _description = 'Vehicle'

    chassis_no = fields.Char('Chasis Number',help = "Unique Chasis number of the vehicle")

    @api.model_create_multi
    def create(self, vals_list):
        active_picking_id = self.env.context.get('active_picking_id', False)
        if active_picking_id:
            picking_id = self.env['stock.picking'].browse(active_picking_id)
            if picking_id and not picking_id.picking_type_id.use_create_lots:
                raise UserError(_('You are not allowed to create a lot or serial number with this operation type. To change this, go on the operation type and tick the box "Create New Lots/Serial Numbers".'))
        return super(ProductionLot, self).create(vals_list)

    @api.multi
    def write(self, vals):
        if 'product_id' in vals and any([vals['product_id'] != lot.product_id.id for lot in self]):
            move_lines = self.env['stock.move.line'].search([('lot_id', 'in', self.ids)])
            if move_lines:
                raise UserError(_(
                    'You are not allowed to change the product linked to a serial or lot number ' +
                    'if some stock moves have already been created with that number. ' +
                    'This would lead to inconsistencies in your stock.'
                ))
        return super(ProductionLot, self).write(vals)

    @api.one
    def _product_qty(self):
        # We only care for the quants in internal or transit locations.
        quants = self.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
        self.product_qty = sum(quants.mapped('quantity'))
