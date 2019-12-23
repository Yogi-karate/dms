# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class VehicleInventoryActions(models.TransientModel):
    _name = "vehicle.inventory.action"
    _description = "Vehicle receipts"
    action = fields.Selection([
        ('allocate', 'Allocate Vehicle'),
        ('deallocate', 'Deallocate Vehicle'),
        ('receipt', 'Recieve Vehicle'),
        ('deliver', 'Deliver Vehicle'),
        ('transfer', 'Transfer Vehicle'),
    ], string='Action', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='receipt')
    vehicle_id = fields.Many2one('vehicle')
    purchase_id = fields.Many2one('purchase.order')
    order_id = fields.Many2one('sale.order')
    location_id = fields.Many2one('stock.location')
    allocation_order_id = fields.Many2one('sale.order')
    destination_location_id = fields.Many2one('stock.location')
    delivery_date = fields.Date("Delivery Date")
    allocation_age = fields.Char("Days Allocated")
    partner_id = fields.Many2one('res.partner', string="Customer")
    transfer_date = fields.Date("Transfer Date")
    product_id = fields.Many2one('product.product', string="product")

    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the vehicle to act on .
            Use context to pick action based default values
            Ensure Vehicle is in stock or transit and allocation status is available
        """
        result = super(VehicleInventoryActions, self).default_get(fields)
        if self._context.get('action') and self._context.get('action') == 'allocate':
            print("*** In allocate Vehicle Default Get ****")
        if self._context.get('active_id'):
            vehicle = self.env['vehicle'].browse(self._context['active_id'])
            print("---- In Active id Vehicle Default Get -------", vehicle)
            if vehicle:
                result['vehicle_id'] = vehicle.id
            if vehicle.delivery_date:
                result['delivery_date'] = vehicle.delivery_date
            if vehicle.order_id:
                result['order_id'] = vehicle.order_id.id
            if vehicle.partner_id:
                result['partner_id'] = vehicle.partner_id.id
            if vehicle.location_id:
                result['location_id'] = vehicle.location_id.id
        return result

    @api.model
    def _default_transfer_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'internale'), ('warehouse_id', '=', False)])
        return types[:1]

    picking_type_id = fields.Many2one('stock.picking.type', 'Transfer To',
                                      required=True, default=_default_transfer_picking_type,
                                      help="This will determine operation type of transfer vehicle")

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
        move_lines = self.sudo().env['stock.move.line'].search(
            ['&', ('picking_id', '=', picking.id), ('product_id', '=', product.id), ('qty_done', '!=', 1)])
        for line in move_lines:
            print("the line in picking------", line, line.state)
        if not move_lines:
            raise UserError(_(
                "Invalid PO - There is a different Product in the Receipt. Product in Vehicle and Purchase order should be same. "))
        if len(move_lines) > 1:
            move_lines[0].write({'qty_done': 1, 'vehicle_id': vehicle.id})
        else:
            move_lines.write({'qty_done': 1, 'vehicle_id': vehicle.id})
        print("picking move lines", picking.move_line_ids_without_package.filtered(lambda l: l.qty_done != 1))
        if not picking.move_line_ids_without_package.filtered(lambda l: l.qty_done != 1):
            picking.action_done()
        vehicle.purchase_id = self.purchase_id
        return

    def action_apply_deliver(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        order_id = vehicle.order_id
        print("the picking in deliver of vehicle ******", order_id, order_id.picking_ids)
        if len(order_id.picking_ids) > 1:
            raise UserError(_("Multiple Pickings. Please go to Sale order screen and receive Manually"))
        if not self.order_id.picking_ids:
            raise UserError(_("Invalid Sale order for this Vehicle"))
        picking = order_id.picking_ids[0]

        if picking.location_id == self.location_id or self.location_id in picking.location_id.child_ids:
            # no move lines as availability is not there try confirming stock move
            move = picking.move_ids_without_package[0]
            if move:
                print("the move is&&&&&", move)
                move._action_confirm() \
                    ._action_assign()

            move_line = picking.move_line_ids[0]
            if not move_line or len(move_line) > 1:
                raise UserError(_(
                    "Could not confirm this delivery order ...please check location and availability:"))
            else:
                print("The location of move line is ", move_line[0].location_id)
                move_line[0].write({'vehicle_id': vehicle.id, 'qty_done': 1})
                picking.action_done()
                vehicle.write({'state': 'sold'})
        else:
            raise UserError(_(
                "The Location of vehicle is not as per sale order.Check vehicle is in location or do a transfer"))
        return

    def action_apply_allocate(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        product_id = vehicle.product_id
        order_product_id = self.allocation_order_id.order_line[0].product_id
        if product_id.id == order_product_id.id:
            vehicle.write({'order_id': self.allocation_order_id.id, 'allocation_state': 'allocated',
                           'allocation_date': fields.Date.today()})
        else:
            raise UserError(_(
                "There is a different Product in the Sale Order. Product in Vehicle and Sale order should be same. "))

        if product_id.id == order_product_id.id:
            vehicle.write({'order_id': self.allocation_order_id.id, 'allocation_state': 'allocated',
                           'allocation_date': fields.Date.today()})
        else:
            raise UserError(_(
                "There is a different Product in the Sale Order. Product in Vehicle and Sale order should be same. "))
        return

    def action_apply_deallocate(self):
        vehicle = self.env['vehicle'].browse(self._context.get('active_ids', []))
        vehicle.write({'allocation_state': 'free', 'allocation_date': False, 'order_id': False})
        return

    def action_apply_transfer(self):
        picking = self._create_transfer_picking()
        picking.action_done()
        return

    @api.model
    def _prepare_picking(self):

        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': False,
            'date': self.transfer_date,
            'origin': self.vehicle_id.name,
            'location_id': self.vehicle_id.location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'company_id': self.vehicle_id.company_id.id,
        }

    @api.multi
    def _create_transfer_picking(self):
        StockPicking = self.env['stock.picking']
        StockMoveLine = self.env['stock.move.line']
        movelines = StockMoveLine.search(
            [('state', '!=', 'done'), ('vehicle_id', '=', self.vehicle_id.id),
             ('picking_id.picking_type_code', '=', 'internal')])
        if movelines:
            raise UserError(_(
                "There is already a transfer order for this vehicle."))
        else:
            res = self._prepare_picking()
            picking = StockPicking.create(res)
            move_vals = self._prepare_stock_moves(picking)
            for move_val in move_vals:
                move  = self.env['stock.move'] \
                    .create(move_val) \
                    ._action_confirm() \
                    ._action_assign()
            if not picking.move_line_ids:
                raise UserError(_(
                    "Could not transfer vehicle. Please check with Administrator"))
            for move_line in picking.move_line_ids:
                move_line.write({'vehicle_id': self.vehicle_id.id, 'qty_done': 1})
            return picking

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        template = {
            'name': self.vehicle_id.name or '',
            'product_id': self.vehicle_id.product_id.id,
            'product_uom': 1,
            'date': fields.Datetime.now(),
            'date_expected': fields.Datetime.now(),
            'location_id': self.vehicle_id.location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'picking_id': picking.id,
            'partner_id': False,
            'state': 'draft',
            'company_id': self.vehicle_id.company_id.id,
            'picking_type_id': self.picking_type_id.id,
            'origin': self.vehicle_id.name,
            'route_ids': self.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.picking_type_id.warehouse_id.id,
            'product_uom_qty': 1,
        }
        res.append(template)
        return res
