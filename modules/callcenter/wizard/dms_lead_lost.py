# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _name = 'dms.lead.lost'
    _description = 'Get Lost Reason'

    lost_reason = fields.Many2one('crm.lost.reason', 'Lost Reason')
    lost_remarks = fields.Char('Remarks')

    @api.multi
    def action_lost_reason_apply(self):
        leads = self.env['dms.vehicle.lead'].browse(self.env.context.get('active_ids'))
        leads.write({'lost_reason': self.lost_reason_id.id,lost_remarks:self.lost_remarks})
        return leads.action_set_lost()
