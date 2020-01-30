# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from odoo.exceptions import UserError

class AssessmentSheet(models.Model):
    _name = 'assessment.sheet'
    booking_id = fields.Many2one('service.booking',required=True)
    active = fields.Boolean('Active',default=True)
    bt_no = fields.Char('BT No')
    date = fields.Datetime('Date')
    partner_name = fields.Char('Customer',required=True)
    partner_mobile = fields.Char('Mobile',required=True
                                 )
    secondary_mobile = fields.Char('Secondary Mobile')
    mail = fields.Char('Mail ID')
    address = fields.Text('Address')
    assets = fields.Many2many('vehicle.asset')
    damages = fields.Many2many('vehicle.damage')
    needle_position = fields.Selection([('F or H','F or H'),('F or H- 3/4','F or H- 3/4'),
                                        ('3/4','3/4'),('3/4-1/2','3/4-1/2'),('1/2','1/2'),
                                        ('1/2-1/4','1/2-1/4'),('1/4','1/4'),('1/4-E or C','1/4-E or C'),
                                        ('E or C','E or C')])
    pick_or_drop = fields.Selection([('pick','Pick'),('drop','Drop')])
    remarks = fields.Text('Remarks')
    dealer_rep_name = fields.Char('Dealer Rep.Name')
    vehicle_id = fields.Many2one('vehicle',compute='_get_vehicle_values',store=True)
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

    @api.depends('booking_id.vehicle_id')
    def _get_vehicle_values(self):
        self._vehicle_values()

    @api.onchange('booking_id.vehicle_id')
    def _vehicle_values(self):
        for sheet in self:
            print(sheet.booking_id.vehicle_id)
            sheet.vehicle_id = sheet.booking_id.vehicle_id.id
            sheet.brand = sheet.booking_id.vehicle_id.company_id.name
            sheet.model = sheet.booking_id.vehicle_id.product_id.product_tmpl_id.name
            sheet.variant = sheet.booking_id.vehicle_id.product_id.variant_value

    @api.depends('vehicle_id','vehicle_id.partner_id','booking_id','booking_id.vehicle_id','booking_id.vehicle_id.partner_id')
    def _get_partner_values(self):
        self._partner_values()

    @api.onchange('vehicle_id','vehicle_id.partner_id','booking_id','booking_id.vehicle_id','booking_id.vehicle_id.partner_id')
    def _partner_values(self):
        for sheet in self:
            vehicle = sheet.booking_id.vehicle_id
            sheet.partner_name = vehicle.partner_id.name
            sheet.partner_mobile = vehicle.partner_id.mobile
            sheet.secondary_mobile = vehicle.partner_id.phone
            sheet.mail = vehicle.partner_id.email
            sheet.address = vehicle.partner_id.street




class VehicleInternalParts(models.Model):
    _name = 'vehicle.asset'
    name = fields.Char('Name')

class VehicleDamages(models.Model):
    _name = 'vehicle.damage'
    name = fields.Char('Name')
