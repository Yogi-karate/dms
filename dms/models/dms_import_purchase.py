# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        print(vals)
        result = super(PurchaseOrder, self).create(vals)
        result.create_import(vals)
        return result

    @api.multi
    def create_import(self,vals):
        print(self)
        if 'confirm' in vals and 'vehicle' in vals:
            print("confirming the order as well !!!! ")
            self.button_confirm()
            template = self._prepare_stock_move_line(result.picking_ids, vals['vehicle'])
            res = self.env['stock.move.line'].create(template)
            self.picking_ids.button_validate()
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