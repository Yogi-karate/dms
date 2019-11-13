# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
class SaleAdvancePaymentInv(models.TransientModel):
    _name = "vehicle.receipt"
    _description = "Vehicle receipts"
    purchase_id = fields.Many2one('purchase.order')
    sale_id = fields.Many2one('sale.order')
    location_id = fields.Many2one('stock.location')

    def action_apply_receive(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        if len(self.purchase_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to purchase order screen and receive Manually"))
        if not self.purchase_id.picking_ids:
            raise UserError(_("Invalid purchase order for this Vehicle"))
        move_line = self.sudo().env['stock.move.line'].search([('picking_id','=',self.purchase_id.picking_ids[0].id),('product_id','=',product.id)])
        if not move_line:
            raise UserError(_("There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'qty_done','=',1})
        return

    def action_apply_deliver(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        if len(self.sale_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to Sale order screen and receive Manually"))
        if not self.sale_id.picking_ids:
            raise UserError(_("Invalid Sale order for this Vehicle"))
        move_line = self.sudo().env['stock.move.line'].search(
            [('vehicle_id', '=',vehicle.id)])
        if not move_line:
            raise UserError(_(
                "There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'qty_done', '=', 1})
        return

    def action_apply_allocate(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        if len(self.sale_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to Sale order screen and receive Manually"))
        if not self.sale_id.picking_ids:
            raise UserError(_("Invalid Sale order for this Vehicle"))
        move_line = self.sudo().env['stock.move.line'].search([('vehicle_id', '=', vehicle.id)])
        if not move_line:
            raise UserError(_(
                "There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'allocated_qty', '=', 1})
        return

    def action_apply_transfer(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        if len(self.sale_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to Sale order screen and receive Manually"))
        if not self.sale_id.picking_ids:
            raise UserError(_("Invalid Sale order for this Vehicle"))
        move_line = self.sudo().env['stock.move.line'].search([('vehicle_id', '=', vehicle.id)])
        if not move_line:
            raise UserError(_(
                "There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'location_id', '=', self.location_id.id})
        return
