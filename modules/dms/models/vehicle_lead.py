from odoo import api, fields, models, _
from datetime import datetime
from odoo import api, fields, models, _
from datetime import datetime

class MailActivity(models.Model):
    _name = "mail.activity"
    _inherit = ['mail.activity']
    customer_name = fields.Char('Customer',compute='_compute_fields')
    mobile = fields.Char('Mobile',compute='_compute_fields')
    lead_id = fields.Many2one('dms.vehicle.lead', string='Lead', compute='_compute_fields')
    partner_name = fields.Char(string='Customer', compute='_compute_fields')
    mobile = fields.Char(string='Mobile', compute='_compute_fields')

    @api.onchange('id')
    def _compute_fields(self):
        for activity in self:
            if activity.res_model == 'dms.vehicle.lead':
                vehicle_lead = self.sudo().env['dms.vehicle.lead'].search([('id','=',activity.res_id)])
                activity.lead_id = vehicle_lead.id
                activity.partner_name = vehicle_lead.partner_name
                activity.mobile = vehicle_lead.mobile
                if vehicle_lead.type == 'lead':
                    print("lead..",vehicle_lead.type)
                activity.customer_name = vehicle_lead.partner_name
                activity.mobile = vehicle_lead.mobile


class VehicleLead(models.Model):
    _name = "dms.vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']

    vehicle_id = fields.Many2many('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                  index=True)

    registration_no = fields.Char('Registration No.',compute='_get_sale_order')
    vin_no = fields.Char('VIN No.',compute='_get_sale_order')
    dos = fields.Char(string='Date of Sale',compute='_get_sale_order')
    @api.model
    def create(self, vals):
        vals['type'] = 'lead'
        print(vals,"****************&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&***********************************")
        result = super(VehicleLead, self).create(vals)
        return result

    @api.one
    def _get_sale_order(self):
        # We only care for the customer if sale order is entered.
        self.vin_no = self.vehicle_id.name
        self.registration_no = self.vehicle_id.registration_no
        self.dos = self.vehicle_id.order_date

    class CrmLeadLost(models.TransientModel):
        _name = 'crm.lead.lost'
        _inherit = ['crm.lead.lost']

        @api.multi
        def action_lost_reason_apply_new(self):
            leads = self.env['dms.vehicle.lead'].browse(self.env.context.get('active_ids'))
            leads.write({'lost_reason': self.lost_reason_id.id})
            return leads.action_set_lost()


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
    service_type = fields.Selection([
        ('first', 'First Free Service'),
        ('second', 'Second Free Service'),
        ('third', 'Third Free Service'),
        ('paid', 'Paid Service'),
        ('ar', 'Accidental Repair'),
        ('rr', 'Running Repair'),
        ('Insurance', 'Insurance'),
    ], string='Service Type', store=True, default='first')
    due_date = fields.Datetime(string='Service Due Date')
    partner_name = fields.Char('Customer name',compute='_lead_values')
    mobile = fields.Char('Customer number',compute='_lead_values')
    mail = fields.Char('Customer Mail ID',compute='_lead_values')
    vehicle_id = fields.Many2one('vehicle')
    vehicle_no = fields.Char('Vehicle no',compute='_lead_values')
    vin_no = fields.Char('VIN Number',compute='_lead_values')
    vehicle_model = fields.Char('Model',compute='_lead_values')
    source = fields.Many2one('utm.source',compute='_lead_values')
    user_id = fields.Many2one('res.users',compute='_lead_values')
    tc_name = fields.Char('TC Name',compute='_lead_values')
    @api.onchange('id')
    def _lead_values(self):
        for booking in self:
            booking.partner_name = booking.lead_id.partner_name
            booking.mobile = booking.lead_id.mobile
            booking.mail = booking.lead_id.email_from
            booking.vehicle_no = booking.vehicle_id.name
            booking.vin_no = booking.vehicle_id.chassis_no
            booking.vehicle_model = booking.vehicle_id.product_id.name
            booking.source = booking.lead_id.source_id
            booking.user_id = booking.lead_id.user_id
            booking.tc_name = booking.user_id.partner_id.name





