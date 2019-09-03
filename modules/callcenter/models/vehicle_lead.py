from odoo import api, fields, models, _


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
        compute='_process_call_status')

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

    @api.depends('activity_date_deadline')
    @api.multi
    def _process_call_status(self):
        for lead in self:
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
    user_id = fields.Many2one('res.users', compute='_lead_values', store=True)
    team_id = fields.Many2one('crm.team', compute='_lead_values', store=True)
    service_type = fields.Char('Service Type', compute='_lead_values', store=True)
    source = fields.Char('Source', compute='_lead_values')
    active = fields.Boolean(default=True)
    call_type = fields.Char('Call Type', compute='_lead_values', store=True)

    @api.onchange('lead_id')
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
            booking.call_type = booking.lead_id.call_type
            print(booking.lead_id.call_type,
                  "..................................................................................................")

    @api.multi
    def restore_booking_lost_action_new(self):
        self.write({'active': True})
        lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
        lead.write({'active': True})


class Insurance(models.Model):
    _name = "insurance.booking"
    _description = "Insurance Booking"
    lead_id = fields.Many2one('dms.vehicle.lead')
    vehicle_id = fields.Many2one('vehicle')
    service_type = fields.Char('Service Type', compute='_lead_values', store=True)
    source = fields.Char('Source', compute='_lead_values')
    active = fields.Boolean(default=True)
    partner_name = fields.Char('Customer name', compute='_lead_values')
    mobile = fields.Char('Customer number', compute='_lead_values')
    alternate_no = fields.Char('Alternate number')
    mail = fields.Char('E-Mail ID', compute='_lead_values')
    address = fields.Char('Address', compute='_lead_values')
    vehicle_model = fields.Char('Model', compute='_lead_values')
    reg_no = fields.Char('Reg no', compute='_lead_values')
    engine_no = fields.Char('Engine No', compute='_lead_values')
    chassis_no = fields.Char('VIN No', compute='_lead_values')
    sale_date = fields.Char('Sale Date', compute='_lead_values')
    policy_no = fields.Char(string='Policy No')
    previous_insurance_company = fields.Many2one('res.bank', string='Previous Insurance Company')
    user_id = fields.Many2one('res.users', compute='_lead_values', store=True)
    team_id = fields.Many2one('crm.team', compute='_lead_values', store=True)
    rollover_company = fields.Many2one('res.bank', string='Current Insurance Company')
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
            booking.address = booking.lead_id.street
            booking.reg_no = booking.vehicle_id.registration_no
            booking.sale_date = booking.lead_id.dos
            if not booking.vehicle_id.chassis_no:
                booking.chassis_no = booking.vehicle_id.name
                booking.engine_no = None
            else:
                booking.engine_no = booking.vehicle_id.name
                booking.chassis_no = booking.vehicle_id.chassis_no

    @api.multi
    def restore_booking_lost_action_new(self):
        self.write({'active': True})
        lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
        lead.write({'active': True})
