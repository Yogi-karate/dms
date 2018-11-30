# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Vehicle(models.Model):
    _name = 'vehicle'
    _inherit = 'stock.production.lot'
    _description = 'Vehicle'
    name = fields.Char(
        'Vehicle Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial'),
        required=True, help="Unique Machine Number")
    chassis_no = fields.Char('Chasis Number',help = "Unique Chasis number of the vehicle")
    order_id = fields.Many2one(
        'sale.order', 'SaleOrder',
        domain=[('state', 'in', ['sale','draft'])], required=True)
    battery_no = fields.Char('Battery Number',help = "Unique Battery number of the vehicle")
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True, compute='_get_customer')

    @api.model_create_multi
    def create(self, vals_list):
        active_picking_id = self.env.context.get('active_picking_id', False)
        if active_picking_id:
            picking_id = self.env['stock.picking'].browse(active_picking_id)
            if picking_id and not picking_id.picking_type_id.use_create_lots:
                raise UserError(_('You are not allowed to create a lot or serial number with this operation type. To change this, go on the operation type and tick the box "Create New Lots/Serial Numbers".'))
        return super(Vehicle, self).create(vals_list)

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
        return super(Vehicle, self).write(vals)

    @api.one
    def _get_customer(self):
        # We only care for the customer if sale order is entered.
        if self.order_id:
            customer_id = self.order_id.partner_id
            self.customer_id = customer_id
