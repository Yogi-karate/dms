# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _name = 'dms.lead.lost'
    _description = 'Get Lost Reason'

    lost_reason = fields.Many2one('crm.lost.reason', 'Lost Reason')
    lost_remarks = fields.Char('Remarks')
    type = fields.Selection([
        ('Service', 'Service'),
        ('Insurance', 'Insurance'),
        ('Vehicle', 'Vehicle'),
        ('Finance', 'Finance'),
    ], string='Lost Model Type', store=True, default='Vehicle')
    model = fields.Char('Model', default='crm.lead')

    @api.model
    def default_get(self, fields):
        result = super(CrmLeadLost, self).default_get(fields)
        print("The context in pop up is ", self._context)
        if self._context.get('active_id') and self._context.get('active_type') == 'lead':
            lead = self.env['crm.lead'].browse(self._context['active_id'])
            result['model'] = 'crm.lead'
            result['type'] = 'Vehicle'
        if self._context.get('active_id') and self._context.get('active_type') == 'vehicle_lead':
            lead = self.env['dms.vehicle.lead'].browse(self._context['active_id'])

            if lead and lead.opportunity_type.name == 'Service':
                result['type'] = 'Service'
            else:
                result['type'] = 'Insurance'

        if self._context.get('active_id') and self._context.get('active_type') == 'service_booking':
            result['type'] = 'Service'
            result['model'] = 'service.booking'
        if self._context.get('active_id') and self._context.get('active_type') == 'insurance_booking':
            result['type'] = 'Insurance'
            result['model'] = 'insurance.booking'
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

    def action_lost_reason_leads(self, lead):
        lead.write({'lost_reason': self.lost_reason.id, 'lost_remarks': self.lost_remarks})
        return lead.action_set_lost()

    @api.multi
    def action_service_booking_lost(self):
        bookings = self.env['service.booking'].browse(self.env.context.get('active_ids'))
        self.action_lost_reason_leads(bookings.lead_id)
        bookings.write({'active': False})

    @api.multi
    def action_insurance_booking_lost(self):
        bookings = self.env['insurance.booking'].browse(self.env.context.get('active_ids'))
        self.action_lost_reason_leads(bookings.lead_id)
        bookings.write({'active': False})
