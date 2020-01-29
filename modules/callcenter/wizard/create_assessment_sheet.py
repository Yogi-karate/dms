# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Booking2Assessment(models.TransientModel):
    _name = 'dms.booking2assessment'
    _description = 'Convert Service Booking to Assessment sheet'

    @api.model
    def default_get(self, fields):

        result = super(Booking2Assessment, self).default_get(fields)
        if self._context.get('active_id'):

            booking = self.env['service.booking'].browse(self._context['active_id'])
            print("////////////////////////////////////////////////////////////////////////////////", booking)
            if booking.id:
                result['booking_id'] = booking.id
            if booking.partner_name:
                result['partner_name'] = booking.partner_name
            if booking.mobile:
                result['partner_mobile'] = booking.mobile
            if booking.lead_id:
                result['vehicle_id'] = booking.lead_id.vehicle_id.id
            if booking.vehicle_id.partner_id.street:
                result['address'] = booking.vehicle_id.partner_id.street

        return result

    partner_name = fields.Char('Customer')
    partner_mobile = fields.Char('Mobile')
    pick_or_drop = fields.Selection([('pick', 'Pick'), ('drop', 'Drop')])
    vehicle_id = fields.Many2one('vehicle')
    address = fields.Text('Address')
    bt_no = fields.Char('BT No')
    date = fields.Datetime('Date')
    booking_id = fields.Many2one('service.booking')

    @api.multi
    def action_apply(self):
        """ Create assessment sheet from booking
        """
        booking_values = {
                'partner_name': self.partner_name,
                'partner_mobile': self.partner_mobile,
                'booking_id': self.booking_id.id,
                'vehicle_id': self.vehicle_id.id,
                'pick_or_drop': self.pick_or_drop,
                'date': self.date,
                'secondary_mobile': self.vehicle_id.partner_id.phone,
                'mail': self.vehicle_id.partner_id.email,
                'address': self.address,
                'bt_no':self.bt_no
            }
        bo = self.env['assessment.sheet'].create(booking_values)
        return
