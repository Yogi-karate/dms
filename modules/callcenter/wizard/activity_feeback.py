# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ActivityFeedback(models.TransientModel):
    _name = 'dms.activity.feedback'
    _description = 'Add Additional Feedback to calls'

    @api.model
    def default_get(self, fields):
        result = super(ActivityFeedback, self).default_get(fields)
        if self._context.get('active_id'):
            lead = self.env['dms.vehicle.lead'].browse(self._context['active_id'])

            if lead.id:
                result['lead_id'] = lead.id
            if lead.activity_ids:
                result['activity_id'] = lead.activity_ids[:1]

        return result

    feedback = fields.Char('Call Feedback')
    feedback_type = fields.Selection([
        ('no_response', 'Not Responding'),
        ('sold_out', 'Vehicle Sold Out'),
    ], string='Service Type', store=True, default='no_response')
    lead_id = fields.Many2one('dms.vehicle.lead')
    activity = fields.Many2one('mail.activity', string="Activity")

    @api.multi
    def action_apply(self):
        print("Applying Action")
        return
