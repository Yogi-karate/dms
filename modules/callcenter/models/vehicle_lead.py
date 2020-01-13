from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class VehicleLead(models.Model):
    _name = "dms.vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']

    vehicle_id = fields.Many2one('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                 required=True,
                                 index=True)
    registration_no = fields.Char('Registration No.', compute='_compute_vehicle_values', store=True)
    vin_no = fields.Char('Chassis No.', compute='_compute_vehicle_values', store=True)
    engine_no = fields.Char('Engine No', compute='_compute_vehicle_values')
    dos = fields.Datetime(string='Date of Sale', compute='_compute_vehicle_values', store=True)
    source = fields.Char('Dealer', compute='_compute_vehicle_values', store=True)
    # service_type = fields.Selection([
    #     ('first', 'First Free Service'),
    #     ('second', 'Second Free Service'),
    #     ('third', 'Third Free Service'),
    #     ('paid', 'Paid Service'),
    #     ('ar', 'Accidental Repair'),
    #     ('rr', 'Running Repair'),
    #     ('Insurance', 'Insurance'),
    # ], string='Service Type', store=True, default='first')
    service_type = fields.Many2one('service.type')
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
    model = fields.Char(string='Vehicle Model', compute='_compute_vehicle_values')
    disposition = fields.Many2one('dms.lead.disposition', string="Disposition")
    partner_id = fields.Many2one('res.partner', compute='_computer_partner', store=True)
    partner_name = fields.Char('Customer', compute='_computer_partner_values', store=True)
    mobile = fields.Char('Mobile', compute='_computer_partner_values', store=True)

    @api.onchange('vehicle_id')
    def _process_insurance_data(self):
        for lead in self:
            lead.insurance_history = lead.vehicle_id.insurance_history

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
            if opportunity.name == 'Insurance':
                pass
                # rec['service_type'] = 'Insurance'
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
            if len(lead.message_ids.filtered(lambda rec: rec.mail_activity_type_id)) == 0 and len(
                    lead.activity_ids) == 0:
                lead.call_state = 'fresh'
            if len(lead.activity_ids.filtered(lambda rec: rec.activity_type_id.name == 'call-back')) > 0:
                lead.call_state = 'call-back'

    @api.depends('vehicle_id.registration_no', 'vehicle_id.source', 'vehicle_id.date_order', 'vehicle_id.chassis_no',
                 'vehicle_id.product_id')
    @api.multi
    def _compute_vehicle_values(self):
        for lead in self:
            lead.registration_no = lead.vehicle_id.registration_no
            lead.model = lead.vehicle_id.product_id.name
            lead.dos = lead.vehicle_id.date_order
            sale_date = lead.vehicle_id.date_order
            lead.vin_no = lead.vehicle_id.chassis_no
            lead.source = lead.vehicle_id.source
            lead.engine_no = lead.vehicle_id.engine_no
            if sale_date:
                today = fields.Datetime.now()
                if sale_date.date().day == 29 and sale_date.date().month == 2:
                    lead.date_deadline = sale_date.date().replace(day=28)
                    lead.date_deadline = lead.date_deadline.replace(year=today.year)
                else:
                    lead.date_deadline = sale_date.date().replace(year=today.year)
        # self.get_values()

    @api.depends('vehicle_id.partner_id')
    def _computer_partner(self):
        for lead in self:
            lead.partner_id = lead.vehicle_id.partner_id

    @api.depends('partner_id.name', 'partner_id.mobile')
    def _computer_partner_values(self):
        for lead in self:
            # if not lead.partner_id:
            #     lead.partner_name = lead.vehicle_id.partner_id.name
            #     lead.mobile = lead.vehicle_id.partner_id.mobile
            # else:
            lead.partner_name = lead.partner_id.name
            lead.mobile = lead.partner_id.mobile

    # @api.onchange('vehicle_id')
    # def get_values(self):
    #     for lead in self:
    #         lead.source = lead.vehicle_id.source
    #         lead.registration_no = lead.vehicle_id.registration_no
    #         lead.vin_no = lead.vehicle_id.chassis_no
    #         lead.dos = lead.vehicle_id.date_order
    #         lead.model = lead.vehicle_id.product_id.name
    #         sale_date = lead.vehicle_id.date_order

    @api.model
    def create(self, vals):
        vals['type'] = 'lead'
        ser_type = self.sudo().env['dms.opportunity.type'].search([('id', '=', vals['opportunity_type'])])

        if ser_type.name == 'Insurance':
            vals['service_type'] = None
        result = super(VehicleLead, self).create(vals)
        return result

    def write(self, vals):
        if 'vehicle_id' in vals:
            raise UserError(
                _("Vehicle related fields can't be changed for an existing Lead. Please create a New Lead."))

        return super(VehicleLead, self).write(vals)

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
    company_id = fields.Many2one('res.company', string='Company')


class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Service Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    lead_id = fields.Many2one('dms.vehicle.lead', required=True)
    vehicle_id = fields.Many2one('vehicle', compute='_get_lead_values', store=True)
    location_id = fields.Many2one('stock.location', string='Preferred location of service', track_visibility='onchange')
    remarks = fields.Char('Remarks')
    dop = fields.Datetime('Date and Time of Pick-Up', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('service.booking'))
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
    ], string='Booking Type', store=True, default='pickup', track_visibility='onchange')

    pick_up_address = fields.Char('Pick-up Address')
    due_date = fields.Datetime(string='Service Due Date')
    partner_name = fields.Char('Customer name', compute='_get_lead_values', store=True)
    mobile = fields.Char('Customer number', compute='_get_lead_values', store=True)
    mail = fields.Char('Customer Mail ID', compute='_get_lead_values', store=True)
    vehicle_model = fields.Char('Model', compute='_get_lead_values', store=True)
    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True)
    service_type = fields.Many2one('service.type', compute='_get_lead_values')
    active = fields.Boolean(default=True)
    reg_no = fields.Char('Registration Number', compute='_get_lead_values')
    status = fields.Selection([
        ('new', 'Pending'),
        ('won', 'Reported'),
        ('lost', 'Not Reported'),
    ], string='Status', store=True, default='new', track_visibility='onchange')

    @api.depends('lead_id')
    def _get_lead_values(self):
        self._lead_values()

    @api.onchange('lead_id')
    def _lead_values(self):
        for booking in self:
            booking.partner_name = booking.lead_id.partner_name
            booking.vehicle_id = booking.lead_id.vehicle_id
            booking.reg_no = booking.lead_id.vehicle_id.registration_no

            booking.mobile = booking.lead_id.mobile
            booking.mail = booking.lead_id.email_from
            booking.vehicle_model = booking.lead_id.vehicle_id.product_id.name
            if not booking.service_type:
                booking.service_type = booking.lead_id.service_type.id

    @api.model
    def create(self, vals):
        duplicate_booking = self.env['service.booking'].search([('lead_id', '=', vals['lead_id'])])
        if not duplicate_booking:
            result = super(ServiceBooking, self).create(vals)
            print("---------------the lead in booking is ------------", result.lead_id)
            values = {
                'service_type': vals['service_type'],
                'type': 'opportunity',
                'date_conversion': fields.Datetime.today(),
                'probability': 100
            }
            result.lead_id.write(values)
            return result
        else:
            raise UserError(
                _("Service booking already existed for this lead. Please go back to that Booking and restore."))

    @api.multi
    def mark_won(self):
        self.write({'status': 'won', 'active': True})

    @api.multi
    def mark_lost(self):
        self.write({'status': 'lost', 'active': False})
        lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
        lead.write({'type': 'lead', 'probability': 40})
    # @api.multi
    # def restore_booking_lost_action_new(self):
    #     self.write({'active': True})
    #     lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
    #     lead.write({'active': True,'type':'lead'})


class InsuranceBooking(models.Model):
    _name = "insurance.booking"
    _description = "Insurance Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    lead_id = fields.Many2one('dms.vehicle.lead', required=True)
    vehicle_id = fields.Many2one('vehicle', compute='_get_lead_values', store=True)
    service_type = fields.Many2one('Service Type')
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
    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True)
    rollover_company = fields.Many2one('res.insurance.company', string='Current Insurance Company')
    previous_idv = fields.Char('Previous IDV')
    idv = fields.Char('IDV')
    prev_final_premium = fields.Char('Prev Final Premium')
    cur_final_premium = fields.Char('Cur Final Premium')
    cur_ncb = fields.Char('Cur NCB')
    prev_ncb = fields.Char('Prev NCB')
    cur_due_date = fields.Datetime(string='Cur Insurance Due Date', track_visibility='onchange')
    prev_due_date = fields.Datetime(string='Prev Insurance Due Date')
    discount = fields.Char('Discount')
    dop = fields.Datetime('Date and Time of Pick-Up', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('insurance.booking'))
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
        ('online_payment', 'Online Payment'),
    ], string='Cur Booking Type', store=True, default='pickup' , track_visibility='onchange')

    pick_up_address = fields.Char('Pick-up Address')
    status = fields.Selection([
        ('lost', 'Lost'),
        ('new', 'New'),
        ('won', 'Won'),
    ], string='Status', store=True, default='new' , track_visibility='onchange')

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
                print("service type doesn't exist")

    @api.model
    def create(self, vals):
        duplicate_booking = self.env['insurance.booking'].search([('lead_id', '=', vals['lead_id'])])
        if not duplicate_booking:
            result = super(InsuranceBooking, self).create(vals)
            values = {
                'type': 'opportunity',
                'date_conversion': fields.Datetime.today(),
                'probability': 100
            }
            result.lead_id.write(values)
            return result
        else:
            raise UserError(
                _("Insurance booking already existed for this lead. Please go back to that Booking and restore."))

    @api.multi
    def mark_won(self):
        self.write({'status': 'won', 'active': True})

    # @api.multi
    # def restore_booking_lost_action_new(self):
    #     self.write({'active': True})
    #     lead = self.sudo().env['dms.vehicle.lead'].browse(self.lead_id.id)
    #     lead.write({'active': True})
