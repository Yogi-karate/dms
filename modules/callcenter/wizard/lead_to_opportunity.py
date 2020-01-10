# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2ServiceBooking(models.TransientModel):
    _name = 'dms.lead2service.booking'
    _description = 'Convert Lead to Service Booking (not in mass)'

    @api.model
    def default_get(self, fields):

        result = super(Lead2ServiceBooking, self).default_get(fields)
        if self._context.get('active_id'):

            lead = self.env['dms.vehicle.lead'].browse(self._context['active_id'])
            print("////////////////////////////////////////////////////////////////////////////////", lead)
            if lead.user_id:
                result['user_id'] = lead.user_id.id
            if lead.id:
                result['lead_id'] = lead.id
            if lead.partner_name:
                result['name'] = lead.partner_name
            if lead.mobile:
                result['mobile'] = lead.mobile
            if lead.service_type:
                result['service_type'] = lead.service_type
            if lead.team_id:
                result['team_id'] = lead.team_id.id

        return result

    name = fields.Char('Customer Name')
    service_type = fields.Many2one('service.type')
    # service_type = fields.Selection([
    #     ('first', 'First Free Service'),
    #     ('second', 'Second Free Service'),
    #     ('third', 'Third Free Service'),
    #     ('paid', 'Paid Service'),
    #     ('ar', 'Accidental Repair'),
    #     ('rr', 'Running Repair'),
    #     ('Insurance', 'Insurance'),
    # ], string='Service Type', store=True, default='first')
    date_follow_up = fields.Date('Follow-Up Date', help="Estimate of the date on which the opportunity will be won.")
    mobile = fields.Char('Mobile')
    user_id = fields.Many2one('res.users', 'Salesperson', index=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', oldname='section_id', index=True)
    dop = fields.Datetime('Date and Time of Pick-Up')
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
    ], string='Booking Type', store=True, default='pickup')
    pick_up_address = fields.Char('Pick-up Address')
    remarks = fields.Char('Remarks')
    location_id = fields.Many2one('stock.location', string='Preferred location of service')
    due_date = fields.Datetime(string='Service Due Date')
    lead_id = fields.Many2one('dms.vehicle.lead')

    @api.multi
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        if not self.dop:
            raise UserError("Please select Appointment Date")
        if not self.location_id:
            raise UserError("Please select a location of service")
        if self.booking_type == 'pickup' and (not self.pick_up_address):
            raise UserError("Please add pickup date and address")
        else:
            booking_values = {
                'partner_name': self.lead_id.partner_name,
                'mobile': self.lead_id.mobile,
                'lead_id': self.lead_id.id,
                'vehicle_id': self.lead_id.vehicle_id.id,
                'location_id': self.location_id.id,
                'remarks': self.remarks,
                'dop': self.dop,
                'booking_type': self.booking_type,
                'pick_up_address': self.pick_up_address,
                'service_type': self.service_type.id,
                'due_date': self.due_date,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'vin_no': self.lead_id.vin_no,
                'vehicle_model': self.lead_id.vehicle_id.product_id.name
            }
        bo = self.env['service.booking'].create(booking_values)
        # return leads[0].redirect_opportunity_view()
        return


class Lead2InsuranceBooking(models.TransientModel):
    _name = 'dms.lead2insurance.booking'
    _description = 'Convert Lead to Insurance Booking (not in mass)'

    @api.model
    def default_get(self, fields):

        result = super(Lead2InsuranceBooking, self).default_get(fields)
        if self._context.get('active_id'):
            lead = self.env['dms.vehicle.lead'].browse(self._context['active_id'])
            print("////////////////////////////////////////////////////////////////////////////////", lead)
            if lead.user_id:
                result['user_id'] = lead.user_id.id
            if lead.id:
                result['lead_id'] = lead.id
            if lead.partner_name:
                result['name'] = lead.partner_name
            if lead.mobile:
                result['mobile'] = lead.mobile
            if lead.team_id:
                result['team_id'] = lead.team_id.id
        return result

    name = fields.Char('Customer Name')
    date_follow_up = fields.Date('Follow-Up Date', help="Estimate of the date on which the opportunity will be won.")
    mobile = fields.Char('Mobile')
    user_id = fields.Many2one('res.users', 'Salesperson', index=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', oldname='section_id', index=True)
    dop = fields.Datetime('Date and Time of Pick-Up')
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
        ('online_payment', 'Pay Online'),
    ], string='Booking Type', store=True, default='pickup')
    pick_up_address = fields.Char('Pick-up Address')
    remarks = fields.Char('Remarks')
    lead_id = fields.Many2one('dms.vehicle.lead')
    alternate_no = fields.Char('Alternate number')
    due_date = fields.Datetime(string='Insurance Due Date')
    policy_no = fields.Char(string='Policy No')
    previous_insurance_company = fields.Many2one('res.insurance.company', string='Previous Insurance Company')
    rollover_company = fields.Many2one('res.insurance.company', string='Current Insurance Company')
    previous_idv = fields.Char('Previous IDV')
    idv = fields.Char('IDV')
    discount = fields.Char('Discount')
    prev_final_premium = fields.Char('Prev Final Premium')
    cur_final_premium = fields.Char('Cur Final Premium')
    cur_ncb = fields.Char('Cur NCB')
    prev_ncb = fields.Char('Prev NCB')
    cur_due_date = fields.Datetime(string='Cur Insurance Due Date')
    prev_due_date = fields.Datetime(string='Prev Insurance Due Date')
    prev_booking_type_insurance = fields.Selection([
        ('nil-dip', 'NIL-DIP'),
        ('comprehensive', 'Comprehensive'),
    ], string='Prev NIL-DIP/Comprehensive', store=True, default='comprehensive')
    cur_booking_type_insurance = fields.Selection([
        ('nil-dip', 'NIL-DIP'),
        ('comprehensive', 'Comprehensive'),
    ], string='Cur NIL-DIP/Comprehensive', store=True, default='comprehensive')

    @api.multi
    def action_apply(self):

        if not self.dop:
            raise UserError("Please select Appointment Date")
        if self.booking_type == 'pickup' and (not self.pick_up_address):
            raise UserError("Please add both pickup date and address")
        booking_values = {
            'lead_id': self.lead_id.id,
            'vehicle_id': self.lead_id.vehicle_id.id,
            'partner_name': self.lead_id.partner_name,
            'mobile': self.lead_id.mobile,
            'dop': self.dop,
            'pre_dip_or_comp': self.prev_booking_type_insurance,
            'cur_dip_or_comp': self.cur_booking_type_insurance,
            'booking_type': self.booking_type,
            'alternate_no': self.alternate_no,
            'pick_up_address': self.pick_up_address,
            'pre_due_date': self.prev_due_date,
            'cur_due_date': self.cur_due_date,
            'policy_no': self.policy_no,
            'previous_insurance_company': self.previous_insurance_company.id,
            'rollover_company': self.rollover_company.id,
            'previous_idv': self.previous_idv,
            'idv': self.idv,
            'user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'prev_final_premium': self.prev_final_premium,
            'cur_final_premium': self.cur_final_premium,
            'pre_ncb': self.prev_ncb,
            'cur_ncb': self.cur_ncb,
            'vehicle_model': self.lead_id.vehicle_id.product_id.name
        }
        bo = self.env['insurance.booking'].create(booking_values)
        # return leads[0].redirect_opportunity_view()
        return
