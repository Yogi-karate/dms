# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Sheet2Order(models.TransientModel):
    _name = 'dms.sheet2order'
    _description = 'Create a repair order from assessment sheet'

    @api.model
    def default_get(self, fields):

        result = super(Sheet2Order, self).default_get(fields)
        if self._context.get('active_id'):

            sheet = self.env['assessment.sheet'].browse(self._context['active_id'])
            if sheet.id:
                result['assessment_id'] = sheet.id
            if sheet.vehicle_id.partner_id:
                result['partner_id'] = sheet.vehicle_id.partner_id.id
            if sheet.partner_mobile:
                result['partner_mobile'] = sheet.partner_mobile

        return result

    partner_id = fields.Many2one('res.partner')
    partner_mobile = fields.Char('Mobile')
    assessment_id = fields.Many2one('assessment.sheet')

    @api.multi
    def action_apply(self):
        """ Create assessment sheet from booking
        """
        booking_values = {
                'assessment_id': self.assessment_id.id,
                'partner_mobile': self.partner_mobile,
                'partner_id': self.assessment_id.vehicle_id.partner_id.id
            }
        bo = self.env['repair.order'].create(booking_values)
        return
