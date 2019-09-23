from odoo import api, fields, models, _
from datetime import datetime, timedelta


class VehicleLead(models.Model):
    _name = "dms.vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']

    vehicle_id = fields.Many2many('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                  index=True)
    registration_no = fields.Char('Registration No.')
    vin_no = fields.Char('Chassis No.')
    dos = fields.Datetime(string='Date of Sale')
    source = fields.Char('Source')
    service_type = fields.Selection([
        ('first', 'First Free Service'),
        ('second', 'Second Free Service'),
        ('third', 'Third Free Service'),
        ('paid', 'Paid Service'),
        ('ar', 'Accidental Repair'),
        ('rr', 'Running Repair'),
        ('Insurance', 'Insurance'),
    ], string='Service Type', store=True, default='first')
    lost_remarks = fields.Char('Remarks')
    call_type = fields.Char('Call Type', compute='_compute_lead_type')
    call_state = fields.Selection([
        ('fresh', 'Fresh'),
        ('done', 'Completed'),
        ('progress', 'In-Progress'),
        ('call-back', 'Callback'),
    ], string='Call Status', readonly=True, track_visibility='onchange', track_sequence=3,
        compute='_process_call_status', store=True)
    current_due_date = fields.Date(string='Current Due-Date', compute='_process_call_status', store=True)
    insurance_history = fields.One2many('vehicle.insurance', string='Current Insurance Data',
                                        compute='_process_insurance_data')
    finance_history = fields.One2many('vehicle.finance', string='Current Finance Data',
                                        compute='_process_insurance_data')
    model = fields.Char(string='Vehicle Model', compute='_process_vehicle_model')
    disposition = fields.Many2one('dms.lead.disposition', string="Disposition")

    @api.multi
    def _process_insurance_data(self):
        for lead in self:
            lead.insurance_history = lead.vehicle_id.insurance_history
            lead.finance_history = lead.vehicle_id.finance_history


    @api.multi
    def _process_vehicle_model(self):
        for lead in self:
            lead.model = lead.vehicle_id.product_id.name

    @api.multi
    def _compute_lead_type(self):
        for lead in self:
            lead.call_type = lead.opportunity_type.name

    @api.model
    def default_get(self, fields):
        rec = super(VehicleLead, self).default_get(fields)
        lead_type = self.env.context.get('default_source_type')
        if lead_type:
            opportunity = self.env['dms.opportunity.type'].search([('name', '=', lead_type)], limit=1)
            rec['opportunity_type'] = opportunity.id
            rec['call_type'] = opportunity.name
        return rec

    @api.depends('activity_ids.date_deadline')
    @api.multi
    def _process_call_status(self):
        for lead in self:
            lead.current_due_date = lead.activity_date_deadline
            if not len(lead.activity_ids) and len(lead.message_ids.filtered(lambda rec: rec.mail_activity_type_id)) > 0:
                lead.call_state = 'done'
            if len(lead.activity_ids) > 0 and len(lead.message_ids.filtered(lambda rec: rec.mail_activity_type_id)) > 0:
                lead.call_state = 'progress'
            if len(lead.message_ids.filtered(lambda rec: rec.mail_activity_type_id)) == 0 or len(
                    lead.activity_ids) == 0:
                lead.call_state = 'fresh'
            if len(lead.activity_ids.filtered(lambda rec: rec.activity_type_id.name == 'call-back')) > 0:
                lead.call_state = 'call-back'

    @api.onchange('vehicle_id')
    def get_values(self):
        for lead in self:
            lead.partner_name = lead.vehicle_id.partner_id.name
            lead.street = lead.vehicle_id.partner_id.street
            lead.source = lead.vehicle_id.source
            lead.mobile = lead.vehicle_id.partner_id.mobile
            lead.phone = lead.vehicle_id.partner_id.phone
            lead.email_from = lead.vehicle_id.partner_id.email
            lead.registration_no = lead.vehicle_id.registration_no
            lead.vin_no = lead.vehicle_id.chassis_no
            lead.dos = lead.vehicle_id.date_order
            sale_date = lead.vehicle_id.date_order
            if sale_date:
                today = fields.Datetime.now()
                lead.date_deadline = sale_date.date().replace(year=today.year)


    @api.model
    def create(self, vals):
        vals['type'] = 'lead'
        result = super(VehicleLead, self).create(vals)
        return result

    @api.multi
    def reassign_users(self, user_id, team_id):
        for lead in self:
            vals = {
                'user_id': user_id,
                'team_id': team_id
            }
            lead.write(vals)


class LostReason(models.Model):
    _name = "crm.lost.reason"
    _inherit = "crm.lost.reason"
    type = fields.Many2one('dms.opportunity.type', string='Reason Type')


class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Service Booking"
    lead_id = fields.Many2one('dms.vehicle.lead', required=True)
    vehicle_id = fields.Many2one('vehicle', compute='_get_lead_values', store=True)
    location_id = fields.Many2one('stock.location', string='Preferred location of service')
    remarks = fields.Char('Remarks')
    dop = fields.Datetime('Date and Time of Pick-Up')

    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
        ('online_payment', 'Online Payment'),
    ], string='Booking Type', store=True, default='pickup')

    pick_up_address = fields.Char('Pick-up Address')
    due_date = fields.Datetime(string='Service Due Date')
    partner_name = fields.Char('Customer name', compute='_get_lead_values', store=True)
    mobile = fields.Char('Customer number', compute='_get_lead_values', store=True)
    mail = fields.Char('Customer Mail ID', compute='_get_lead_values', store=True)
    vehicle_model = fields.Char('Model', compute='_get_lead_values', store=True)
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
                              default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True, track_visibility='onchange')
    service_type = fields.Char('Service Type')
    active = fields.Boolean(default=True)

    @api.depends('lead_id')
    def _get_lead_values(self):
        self._lead_values()

    @api.onchange('lead_id')
    def _lead_values(self):
        for booking in self:
            booking.partner_name = booking.lead_id.partner_name
            booking.vehicle_id = booking.lead_id.vehicle_id
            booking.mobile = booking.lead_id.mobile
            booking.mail = booking.lead_id.email_from
            booking.vehicle_model = booking.lead_id.vehicle_id.product_id.name
            if not booking.service_type:
                booking.service_type = booking.lead_id.service_type

    @api.model
    def create(self, vals):
        result = super(ServiceBooking, self).create(vals)
        print("---------------the lead in booking is ------------", result.lead_id)
        values = {
            'service_type': result.service_type,
            'type': 'opportunity',
            'date_conversion': fields.Datetime.today(),
            'probability': 100
        }
        result.lead_id.write(values)
        return result

    @api.multi
    def restore_booking_lost_action_new(self):
        self.write({'active': True})
        lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
        lead.write({'active': True})


class InsuranceBooking(models.Model):
    _name = "insurance.booking"
    _description = "Insurance Booking"
    lead_id = fields.Many2one('dms.vehicle.lead', required=True)
    vehicle_id = fields.Many2one('vehicle', compute='_get_lead_values', store=True)
    service_type = fields.Char('Service Type')
    active = fields.Boolean(default=True)
    partner_name = fields.Char('Customer name', compute='_update_booking_values', store=True)
    mobile = fields.Char('Customer number', compute='_update_booking_values', store=True)
    alternate_no = fields.Char('Alternate number')
    mail = fields.Char('E-Mail ID', compute='_update_booking_values', store=True)
    address = fields.Char('Address', compute='_update_booking_values', store=True)
    vehicle_model = fields.Char('Model', compute='_update_booking_values', store=True)
    reg_no = fields.Char('Reg no', compute='_update_booking_values', store=True)
    sale_date = fields.Char('Sale Date', compute='_update_booking_values', store=True)
    policy_no = fields.Char(string='Policy No')
    previous_insurance_company = fields.Many2one('res.insurance.company', string='Previous Insurance Company')
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
                              default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True, track_visibility='onchange')
    rollover_company = fields.Many2one('res.insurance.company', string='Current Insurance Company')
    previous_idv = fields.Char('Previous IDV')
    idv = fields.Char('IDV')
    prev_final_premium = fields.Char('Prev Final Premium')
    cur_final_premium = fields.Char('Cur Final Premium')
    cur_ncb = fields.Char('Cur NCB')
    prev_ncb = fields.Char('Prev NCB')
    cur_due_date = fields.Datetime(string='Cur Insurance Due Date')
    prev_due_date = fields.Datetime(string='Prev Insurance Due Date')
    discount = fields.Char('Discount')
    dop = fields.Datetime('Date and Time of Pick-Up')

    cur_dip_or_comp = fields.Selection([
        ('nil-dip', 'NIL-DIP'),
        ('comprehensive', 'Comprehensive'),
    ], string='Prev NIL-DIP/Comprehensive', store=True, default='comprehensive')
    prev_dip_or_comp = fields.Selection([
        ('nil-dip', 'NIL-DIP'),
        ('comprehensive', 'Comprehensive'),
    ], string='Prev NIL-DIP/Comprehensive', store=True, default='comprehensive')
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
    ], string='Cur Booking Type', store=True, default='pickup')

    pick_up_address = fields.Char('Pick-up Address')

    @api.depends('lead_id')
    def _update_booking_values(self):
        self._lead_values()

    @api.onchange('lead_id')
    def _lead_values(self):
        for booking in self:
            booking.vehicle_id = booking.lead_id.vehicle_id
            booking.partner_name = booking.lead_id.partner_name
            booking.mobile = booking.lead_id.mobile
            booking.mail = booking.lead_id.email_from
            booking.vehicle_model = booking.vehicle_id.product_id.name
            booking.address = booking.lead_id.street
            booking.reg_no = booking.vehicle_id.registration_no
            booking.sale_date = booking.lead_id.dos
            if not booking.service_type:
                booking.service_type = booking.lead_id.service_type

    @api.model
    def create(self, vals):
        result = super(InsuranceBooking, self).create(vals)
        values = {
            'service_type': result.service_type,
            'type': 'opportunity',
            'date_conversion': fields.Datetime.today(),
            'probability': 100
        }
        result.lead_id.write(values)
        return result

    @api.multi
    def restore_booking_lost_action_new(self):
        self.write({'active': True})
        lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
        lead.write({'active': True})
