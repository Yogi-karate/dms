# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _name = 'dms.lead.lost'
    _description = 'Get Lost Reason'

    lost_reason = fields.Many2one('crm.lost.reason', 'Lost Reason')
    lost_remarks = fields.Char('Remarks')
    type = fields.Selection([
        ('Vehicle', 'Vehicle'),
        ('Service', 'Service'),
        ('Insurance', 'Insurance'),
    ], string='Lost Model Type', store=True, default='Vehicle')
    model = fields.Char('Model', default='dms.vehicle.lead')

    @api.model
    def default_get(self, fields):
        result = super(CrmLeadLost, self).default_get(fields)
        print("The context in pop up is ", self._context)
        if self._context.get('active_type') == 'lead' or self._context.get('active_type') == 'vehicle_lead':
            lead = self.env[self._context.get('active_model')].browse(self._context['active_id'])
        if self._context.get('active_type') == 'insurance_booking' or self._context.get('active_type') == 'service_booking':
            lead = self.env[self._context.get('active_model')].browse(self._context['active_id']).lead_id
        if not lead:
            return
        if lead.opportunity_type.name == 'Vehicle':
            result['type'] = 'Vehicle'
        if lead.opportunity_type.name == 'Service':
            result['type'] = 'Service'
        if lead.opportunity_type.name == 'Insurance':
            result['type'] = 'Insurance'

        return result

    @api.multi
    def action_lost_reason(self):
        model = self._context.get('active_model')
        if model == 'dms.vehicle.lead' or model == 'crm.lead':
            lead = self.env[model].browse(self.env.context.get('active_ids'))
        else:
            booking = self.env[model].browse(self.env.context.get('active_ids'))
            booking.write({'active': False,'status':'lost'})
            lead = booking.lead_id
            lead.write({'type':'lead','probability':40})
            return
        if not lead:
            return
        lead.write({'lost_reason': self.lost_reason.id, 'lost_remarks': self.lost_remarks})
        return lead.action_set_lost()
