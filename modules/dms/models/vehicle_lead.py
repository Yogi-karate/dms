from odoo import api, fields, models, _
from datetime import datetime
from odoo import api, fields, models, _
from datetime import datetime


class MailActivity(models.Model):
    _name = "mail.activity"
    _inherit = ['mail.activity']
    customer_name = fields.Char('Customer', compute='_compute_fields')
    mobile = fields.Char('Mobile', compute='_compute_fields')
    lead_id = fields.Many2one('dms.vehicle.lead', string='Lead', compute='_compute_fields')
    partner_name = fields.Char(string='Customer', compute='_compute_fields')
    mobile = fields.Char(string='Mobile', compute='_compute_fields')

    @api.onchange('id')
    def _compute_fields(self):
        for activity in self:
            if activity.res_model == 'dms.vehicle.lead':
                vehicle_lead = self.sudo().env['dms.vehicle.lead'].search([('id', '=', activity.res_id)])
                activity.lead_id = vehicle_lead.id
                activity.partner_name = vehicle_lead.partner_name
                activity.mobile = vehicle_lead.mobile
                if vehicle_lead.type == 'lead':
                    print("lead..", vehicle_lead.type)
                activity.customer_name = vehicle_lead.partner_name
                activity.mobile = vehicle_lead.mobile



class VehicleLead(models.Model):
    _name = "dms.vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']

    vehicle_id = fields.Many2many('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                  index=True)

    registration_no = fields.Char('Registration No.')
    vin_no = fields.Char('Chassis No.')
    dos = fields.Datetime(string='Date of Sale')
    source = fields.Char('Source', compute='_get_sale_order')
    service_type = fields.Selection([
        ('first', 'First Free Service'),
        ('second', 'Second Free Service'),
        ('third', 'Third Free Service'),
        ('paid', 'Paid Service'),
        ('ar', 'Accidental Repair'),
        ('rr', 'Running Repair'),
        ('Insurance', 'Insurance'),
    ], string='Service Type', store=True, default='first')
    dms_lost_reason = fields.Many2one('dms.lost.reason', string='Lost Reason')
    lost_remarks = fields.Char('Remarks')

    @api.model
    def create(self, vals):
        vals['type'] = 'lead'
        print(vals, "****************&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&***********************************")
        result = super(VehicleLead, self).create(vals)
        return result

    @api.one
    def _get_sale_order(self):
        # We only care for the customer if sale order is entered.
        self.source = self.vehicle_id.source

class CrmLeadLost(models.TransientModel):
        _name = 'crm.lead.lost'
        _inherit = ['crm.lead.lost']
        dms_lost_reason = fields.Many2one('dms.lost.reason',string='Lost Reason')
        lost_remarks = fields.Char('Remarks')

        @api.multi
        def action_lost_reason_apply_new(self):
            leads = self.env['dms.vehicle.lead'].browse(self.env.context.get('active_ids'))
            leads.write({'lost_reason': self.lost_reason_id.id,'dms_lost_reason':self.dms_lost_reason.id,'lost_remarks':self.lost_remarks})
            return leads.action_set_lost()

        def action_lost_reason_leads(self,leads):
            leads.write({'lost_reason': self.lost_reason_id.id,'dms_lost_reason':self.dms_lost_reason.id,'lost_remarks':self.lost_remarks})
            return leads.action_set_lost()

        @api.multi
        def action_booking_reason_apply_new(self):
            bookings = self.env['service.booking'].browse(self.env.context.get('active_ids'))
            self.action_lost_reason_leads(bookings.lead_id)
            bookings.write({'active': False})



        @api.multi
        def reassign_users(self, user_id, team_id):
            for enquiry in self:
                vals = {
                    'user_id': user_id,
                    'team_id': team_id
                }
                enquiry.write(vals)


class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Service Booking"
    lead_id = fields.Many2one('dms.vehicle.lead')
    location_id = fields.Many2one('stock.location', string='Preferred location of service')
    remarks = fields.Char('Remarks')
    dop = fields.Datetime('Date and Time of Pick-Up')
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
    ], string='Booking Type', store=True, default='pickup')
    pick_up_address = fields.Char('Pick-up Address')
    due_date = fields.Datetime(string='Service Due Date')
    partner_name = fields.Char('Customer name', compute='_lead_values')
    mobile = fields.Char('Customer number', compute='_lead_values')
    mail = fields.Char('Customer Mail ID', compute='_lead_values')
    vehicle_id = fields.Many2one('vehicle')
    vin_no = fields.Char('Chassis Number')
    vehicle_model = fields.Char('Model', compute='_lead_values')
    user_id = fields.Many2one('res.users', compute='_lead_values',store=True)
    team_id = fields.Many2one('crm.team', compute='_lead_values',store=True)
    service_type = fields.Char('Service Type', compute='_lead_values', store=True)
    source = fields.Char('Source',compute='_lead_values')
    active = fields.Boolean(default=True)

    @api.onchange('id')
    def _lead_values(self):
        for booking in self:
            booking.partner_name = booking.lead_id.partner_name
            booking.mobile = booking.lead_id.mobile
            booking.mail = booking.lead_id.email_from
            booking.vehicle_model = booking.vehicle_id.product_id.name
            booking.source = booking.lead_id.source
            booking.user_id = booking.lead_id.user_id
            booking.team_id = booking.lead_id.team_id
            booking.service_type = booking.lead_id.service_type

    @api.multi
    def restore_booking_lost_action_new(self):
        print(self)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(self)
        self.write({'active': True})
        lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
        lead.write({'active': True})

class LostReason(models.Model):
    _name = "dms.lost.reason"
    _inherit = ["crm.lost.reason"]
    _description = 'Dms Lost Reason'


