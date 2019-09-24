# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AssignVehicleInStock(models.TransientModel):
    """
        Merge opportunities together.
        If we're talking about opportunities, it's just because it makes more sense
        to merge opps than leads, because the leads are more ephemeral objects.
        But since opportunities are leads, it's also possible to merge leads
        together (resulting in a new lead), or leads and opps together (resulting
        in a new opp).
    """

    _name = 'stock.move.assign.vehicle'
    _description = 'assign vehicles in receipts and delivery'
    vehicle_id = fields.Many2one('vehicle', string='Vehicle', help='Move line Associated to a specific vehicle')
    product_id = fields.Many2one('product.product')
    arr = []
    @api.model
    def default_get(self, fields):
        """ Use active_ids from the context to fetch the leads/opps to merge.
            In order to get merged, these leads/opps can't be in 'Dead' or 'Closed'
        """
        stock = None
        if self._context.get('active_id'):
            stock = self.env['stock.picking'].browse(self._context['active_id'])
            prod = self.env['product.product'].browse(self._context['active_id'])
        for x in self:
            x.product_id = stock.product_id.id
        print("yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",stock.product_id)
        print(stock.product_id.display_name)
        record_ids = self._context.get('active_ids')
        result = super(AssignVehicleInStock, self).default_get(fields)
        self.arr.append(stock.product_id.id)
        print(self.product_id,"----prod")
        if record_ids:
            print(record_ids)
        print("________________",self)
        result['product_id'] = stock.product_id.id
        print(result)
        print("yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
        return result

    @api.multi
    def action_apply(self):
        print("Hello from reassign",self)
        print(self.vehicle_id,"------------------------")
        stoc = self.env['stock.picking'].browse(self._context['active_id'])
        stoc.move_lines._action_assign_new(self.vehicle_id.lot_id)
        if stoc.move_lines.move_line_ids.reference[3]== 'O':
            stoc.move_lines.move_line_ids.update({'vehicle_id_delivery':self.vehicle_id,'lots_visible':True})
        else:
            stoc.move_lines.move_line_ids.update({'vehicle_id_receipt': self.vehicle_id,'lots_visible':True})
        print(stoc.show_lots_text,"hhhhhhhhhhhhhhhhhhhhvisible")
        for x in stoc.move_lines:
            print(x.move_line_ids.id)
        print("selffff.........")