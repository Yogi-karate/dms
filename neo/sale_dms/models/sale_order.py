# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order', 'utm.mixin']

    #user = fields.Many2one('res.partner', compute='_compute_consultant')
    user_name = fields.Char(compute='_compute_consultant')
    user_mobile = fields.Char(compute='_compute_consultant')

    @api.depends('name')
    def _compute_consultant(self):
        """ Compute difference between create date and open date """
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&7")
        user = self.env['res.users'].sudo().search([('id', '=', self.user_id.id)])
        self.user_name = user.partner_id.name
        if user.partner_id.mobile:
            self.user_mobile = user.partner_id.mobile
        else:
            self.user_mobile = user.partner_id.phone

