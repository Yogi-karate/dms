from odoo import api, fields, models, _
from datetime import datetime

class VehicleLead(models.Model):
    _name = "dms.vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']

    vehicle_id = fields.Many2many('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                  index=True)
    service_type = fields.Selection([
        ('first', 'First Free Service'),
        ('second', 'Second Free Service'),
        ('third', 'Third Free Service'),
        ('paid', 'Paid Service'),
        ('ar', 'Accidental Repair'),
        ('rr', 'Running Repair'),
        ('Insurance', 'Insurance'),
    ], string='Service Type', store=True, default='first')
    registration_no = fields.Char('Registration No.',compute='_get_sale_order')
    vin_no = fields.Char('VIN No.',compute='_get_sale_order')
    dos = fields.Char(string='Date of Sale',compute='_get_sale_order')
    due_date = fields.Datetime(string='Due Date')
    location_id = fields.Many2one('stock.location',string='Preferred location of service')
    remarks = fields.Char('Remarks')
    date_follow_up = fields.Date('Follow-Up Date', help="Estimate of the date on which the opportunity will be won.")
    dop = fields.Datetime('Date and Time of Pick-Up')
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
    ], string='Booking Type', store=True, default='pickup')
    pick_up_address = fields.Char('Pick-up Address')
    lead_id = fields.Many2one('crm.lead','Lead')
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
