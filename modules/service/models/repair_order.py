# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError

class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Service Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']


class RepairOrder(models.Model):
    _name = 'repair.order'
    _inherit = ['sale.order']
    assessment_id = fields.Many2one('assessment.sheet')
    name  = fields.Char('name')
    order_line = fields.One2many('repair.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)

    @api.onchange('assessment_id')
    def _get_partner(self):
        self.partner_id = self.assessment_id.vehicle_id.partner_id.id

class SaleOrderLine(models.Model):
    _name = 'repair.order.line'
    _description = 'Repair Order Line'
    _inherit = ['sale.order.line']
    order_id = fields.Many2one('repair.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False, readonly=True)