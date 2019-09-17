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
                activity = lead.activity_ids[:1]
                result['activity_id'] = activity.id
                result['summary'] = activity.summary
                result['date_deadline'] = activity.date_deadline
                result['note'] = activity.note
        return result

    feedback = fields.Char('Call Feedback')
    disposition = fields.Many2one('dms.lead.disposition', string="Disposition")
    lead_id = fields.Many2one('dms.vehicle.lead')
    activity_id = fields.Many2one('mail.activity', string="Activity")
    summary = fields.Char('Summary')
    date_deadline = fields.Date('Follow-Up Date')
    note = fields.Html('Note')

    @api.multi
    def action_apply(self):
        print("Applying Action")
        message = self.activity_id.action_feedback(self.feedback)
        if message:
            self.lead_id.write({'disposition': self.disposition.id})
        return

    @api.multi
    def action_reschedule(self):
        print("Applying Rescedule")
        self.activity_id.action_feedback(self.feedback)
        return
