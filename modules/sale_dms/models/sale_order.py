# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order', 'utm.mixin']

    sales_person_name = fields.Char(compute='_compute_consultant')
    mobile_no = fields.Char(compute='_compute_consultant')

    @api.depends('user_id')
    def _compute_consultant(self):
        """ Compute difference between create date and open date """
        user = self.sudo().env['res.partner'].search([('id', '=', self.user_id.partner_id.id)])
        print(self.user_id.partner_id)
        # print(user.name,"{{{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        self.sales_person_name = user.name
        if user.mobile:
            self.mobile_no = user.mobile
        else:
            self.mobile_no = user.phone

