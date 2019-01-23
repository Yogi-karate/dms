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
