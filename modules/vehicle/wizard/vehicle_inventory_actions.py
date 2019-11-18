# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class VehicleInventoryActions(models.TransientModel):
    _name = "vehicle.inventory.action"
    _description = "Vehicle receipts"
    action = fields.Selection([
        ('allocation', 'Allocate Vehicle'),
        ('deallocation', 'Deallocate Vehicle'),
        ('receipt', 'Recieve Vehicle'),
        ('deliver', 'Deliver Vehicle'),
        ('transfer', 'Transfer Vehicle'),
    ], string='Action', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='receipt')
    purchase_id = fields.Many2one('purchase.order')
    order_id = fields.Many2one('sale.order')
    new_order_id = fields.Many2one('sale.order')
    allocation_order_id = fields.Many2one('sale.order')
    location_id = fields.Many2one('stock.location')
    delivery_date = fields.Date("Delivery Date")
    allocation_age = fields.Char("Days Allocated")
    partner_id = fields.Many2one('res.partner')

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the vehicle to act on .
            Use context to pick action based default values
            Ensure Vehicle is in stock or transit and allocation status is available
        """
        result = super(VehicleInventoryActions, self).default_get(fields)
        if self._context.get('source') and self._context.get('source') == 'allocate':
            print("*** In allocate Vehicle Default Get ****")
        if self._context.get('active_id'):
            vehicle = self.env['vehicle'].browse(self._context['active_id'])
            print("---- In Active id Vehicle Default Get -------", vehicle)
            if vehicle.delivery_date:
                result['delivery_date'] = vehicle.delivery_date
            if vehicle.order_id:
                result['order_id'] = vehicle.order_id
            if vehicle.partner_id:
                result['partner_id'] = vehicle.partner_id
        return result

    def action_apply_receive(self):
        print("the  active ids is", self._context.get('active_ids', []))
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        print("the vehicle and product are ", vehicle, product)
        if len(self.purchase_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to purchase order screen and receive Manually"))
        if not self.purchase_id.picking_ids:
            raise UserError(_("Invalid purchase order for this Vehicle"))
        picking = self.purchase_id.picking_ids[0]
        move_line = self.sudo().env['stock.move.line'].search(
            [('picking_id', '=', picking.id), ('product_id', '=', product.id)])
        if not move_line:
            raise UserError(_(
                "There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'qty_done': 1, 'vehicle_id': vehicle.id})
        picking.action_done()
        return

    def action_apply_deliver(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        if len(self.order_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to Sale order screen and receive Manually"))
        if not self.order_id.picking_ids:
            raise UserError(_("Invalid Sale order for this Vehicle"))
        move_line = self.sudo().env['stock.move.line'].search(
            [('vehicle_id', '=', vehicle.id)])
        if not move_line:
            raise UserError(_(
                "There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'vehicle_id': vehicle.id, 'qty_done': 1})
        return

    def action_apply_allocate(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        vehicle.write({'order_id': self.allocation_order_id, 'allocation_state': 'allocated',
                       'allocated_date': fields.Datetime.now()})
        return

    def action_apply_deallocate(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        vehicle.write({'allocation_state': 'free', 'allocated_date': False, 'order_id': False})
        return

    def action_apply_transfer(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product = vehicle.product_id
        if len(self.order_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to Sale order screen and receive Manually"))
        if not self.order_id.picking_ids:
            raise UserError(_("Invalid Sale order for this Vehicle"))
        move_line = self.sudo().env['stock.move.line'].search([('vehicle_id', '=', vehicle.id)])
        if not move_line:
            raise UserError(_(
                "There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        move_line.write({'location_id': self.location_id.id})
        return

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }

    @api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': order},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return True
