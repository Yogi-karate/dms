# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'

    @api.multi
    def action_multi_confirm(self):
        auto = self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting')
        for order in self.filtered(lambda order: order.state not in ['sale']):
            order.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
            })
            order._action_confirm()
            if auto:
                order.action_done()
        return True

    @api.model
    def create(self, vals):
        print(vals)
        result = super(SaleOrder, self).create(vals)
        self.create_import(result,vals)
        return result

    @api.multi
    def create_import(self,result,vals):
        print(result)
        if 'confirm' in vals and 'vehicle' in vals:
            print("confirming the order as well !!!! ")
            result.action_confirm()
            template = self._prepare_stock_move_line(result.picking_ids, vals['vehicle'])
            res = self.env['stock.move.line'].create(template)
            result.picking_ids.button_validate()
            print(res)


    @api.multi
    def _prepare_stock_move_line(self, picking,vehicle_name):
        vehicle = self.env['vehicle'].search([('name','=',vehicle_name)])
        if not vehicle:
            print("Could not find vehicle")
            return
        move_line = picking.move_lines
        template = {'move_id':move_line.id,
                    'location_id':move_line.location_id.id,
                    'location_dest_id':move_line.location_dest_id.id,
                    'product_id':move_line.product_id.id,
                    'product_uom_id':1,'picking_id':picking.id,
                    'vehicle_id':vehicle.id,
                    'qty_done':1
                    }
        return template
