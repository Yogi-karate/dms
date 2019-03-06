# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api,fields, models

_logger = logging.getLogger(__name__)

class MassConfirm(models.TransientModel):

    _name = "mass.order.confirm"
    order_no = fields.Char("Order No")
    vehicle_no = fields.Char("Vehicle No")

    @api.multi
    def confirm_inventory(self, val_list):
        _logger.info("Confirm Multi Inventory")
        for vals in val_list:
            _logger.info(vals)
            order_id = vals['ids']
            _logger.info("ORDER ID Before Processing"+str(order_id))
            vehicle_id = self.env['vehicle'].search([('ref', '=', order_id.name)])
            if not vehicle_id or not order_id:
                _logger.error("ERROR processing" + str(order_id))
                continue
            try:
                self._create_move_lines(order_id.picking_ids, vehicle_id.id)
            except Exception as ex:
                _logger.error("ERROR processing" + str(order_id))
        return True


    @api.model
    def confirm_purchase_orders(self, val_list):
        ids = [val['order_no'] for val in val_list]
        _logger.info("The ids multi in purchase confirm")
        _logger.info(ids)
        po_ids = self.env['purchase.order'].search([('name', 'in', ids),('state','=','draft')])
        if po_ids:
            po_ids.button_approve()
            d = val_list
            for l in range(len(po_ids)):
                d[l]['ids'] = po_ids[l]
            self.confirm_inventory(d)
        else:
            _logger.info("No Purchase Inventory to Process")
            return False

    @api.model
    def confirm_sale_orders(self, val_list):
        ids = [val['order_no'] for val in val_list]
        so_ids = self.env['sale.order'].search([('name', 'in', ids),('state','=','draft')])
        if so_ids:
            for so_id in so_ids:
                so_id.action_confirm()
            d = val_list
            for l in range(len(so_ids)):
                d[l]['ids'] = so_ids[l]
            self.confirm_inventory(d)
        else:
            _logger.info("No Sales Inventory to Process")
            return False


    @api.multi
    def _create_move_lines(self, picking_ids, vehicle_id):
        if not picking_ids.move_line_ids:
            template = self._prepare_stock_move_line(picking_ids, vehicle_id)
            res = self.env['stock.move.line'].create(template)
            _logger.info(res)
        else:
            _logger.info("Move Line Exists")
            picking_ids.move_line_ids.write({'vehicle_id':vehicle_id, 'qty_done':1})
        picking_ids.action_done()

    @api.multi
    def _prepare_stock_move_line(self, picking,vehicle_id):

        move_line = picking.move_lines
        template = {'move_id':move_line.id,
                    'location_id':move_line.location_id.id,
                    'location_dest_id':move_line.location_dest_id.id,
                    'product_id':move_line.product_id.id,
                    'product_uom_id':1,'picking_id':picking.id,
                    'vehicle_id':vehicle_id,
                    'qty_done':1
                    }
        return template