# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError

class AssessmentSheet(models.Model):
    _name = 'assessment.sheet'
    booking_id = fields.Many2one('service.booking')
    active = fields.Boolean('Active',default=True)
    bt_no = fields.Char('BT No')
    date = fields.Datetime('Date')
    partner_name = fields.Char('Customer')
    partner_mobile = fields.Char('Mobile')
    secondary_mobile = fields.Char('Secondary Mobile')
    mail = fields.Char('Mail ID')
    address = fields.Text('Address')
    internal_parts = fields.Many2many('vehicle.internal.part')
    damages = fields.Many2many('vehicle.damage')
    needle_position = fields.Selection([('F or H','F or H'),('F or H- 3/4','F or H- 3/4'),
                                        ('3/4','3/4'),('3/4-1/2','3/4-1/2'),('1/2','1/2'),
                                        ('1/2-1/4','1/2-1/4'),('1/4','1/4'),('1/4-E or C','1/4-E or C'),
                                        ('E or C','E or C')])
    pick_or_drop = fields.Selection([('pick','Pick'),('drop','Drop')])
    remarks = fields.Text('Remarks')
    dealer_rep_name = fields.Char('Dealer Rep.Name')
    vehicle_id = fields.Many2one('vehicle')
    company_id = fields.Many2one('res.company')
    brand = fields.Char('Brand',compute='_get_vehicle_values')
    model = fields.Char('Model',compute='_get_vehicle_values')
    variant = fields.Char('Variant',compute='_get_vehicle_values')
    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True)

    @api.depends('vehicle_id')
    def _get_vehicle_values(self):
        self._vehicle_values()

    @api.onchange('vehicle_id')
    def _vehicle_values(self):
        for sheet in self:
            sheet.brand = sheet.vehicle_id.company_id.name
            sheet.model = sheet.vehicle_id.product_id.product_tmpl_id.name
            sheet.variant = sheet.vehicle_id.product_id.variant_value
            sheet.partner_name = sheet.vehicle_id.partner_id.name
            sheet.partner_mobile = sheet.vehicle_id.partner_id.mobile
            sheet.secondary_mobile = sheet.vehicle_id.partner_id.phone
            sheet.mail = sheet.vehicle_id.partner_id.email

            sheet.address = sheet.vehicle_id.partner_id.street
        # for booking in self:
        #     booking.partner_name = booking.lead_id.partner_name
        #     booking.vehicle_id = booking.lead_id.vehicle_id
        #     booking.reg_no = booking.lead_id.vehicle_id.registration_no
        #
        #     booking.mobile = booking.lead_id.mobile
        #     booking.mail = booking.lead_id.email_from
        #     booking.vehicle_model = booking.lead_id.vehicle_id.product_id.name


class VehicleInternalParts(models.Model):
    _name = 'vehicle.internal.part'
    name = fields.Char('Name')

class VehicleDamages(models.Model):
    _name = 'vehicle.damage'
    name = fields.Char('Name')
