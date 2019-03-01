# -*- coding: utf-8 -*-
# Part of Saboo DMS. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, tools, SUPERUSER_ID


class DmsLead(models.Model):
    _name = "crm.lead"
    _inherit = 'crm.lead'

    date_deadline = fields.Date('Follow-Up Date', help="Estimate of the date on which the opportunity will be won.")
    days_open = fields.Float(compute='_compute_days_open', string='Days Open', store=True)
    enquiry_id = fields.Many2one('dms.enquiry',string='Enquiry')
    opportunity_type = fields.Many2one('dms.opportunity.type', string='Opportunity Type')
    color_value = fields.Char(compute='_compute_color',string='Color',help ='true')
    variant_value = fields.Char(compute='_compute_variant',string='Variant',help ='true')
    vehicle_name = fields.Char(compute='_compute_vehicle',string='Vehicle',help ='true')
    team_lead = fields.Char(compute='_compute_lead',string = 'Team Lead')
    
    @api.depends('date_open')
    def _compute_days_open(self):
        """ Compute difference between create date and open date """
        for lead in self.filtered(lambda l: l.date_open and l.create_date):
            date_create = fields.Datetime.from_string(lead.create_date)
            # date_open = fields.Datetime.from_string(lead.date_open)
            lead.days_open = abs((fields.Datetime.now() - date_create).days)

    @api.depends('enquiry_id')
    def _compute_color(self):
        """ Compute color """
        for lead in self.filtered(lambda l: l.enquiry_id):
            lead.color_value = lead.enquiry_id.product_color.name

    @api.depends('enquiry_id')
    def _compute_variant(self):
        """ Compute Variant """
        for lead in self.filtered(lambda l: l.enquiry_id):
            lead.variant_value = lead.enquiry_id.product_variant.name

    @api.depends('enquiry_id')
    def _compute_vehicle(self):
        """ Compute Vehicle/Product ID """
        for lead in self.filtered(lambda l: l.enquiry_id):
            lead.vehicle_name = lead.enquiry_id.product_id.name
    @api.depends('team_id')
    def _compute_lead(self):
        for lead in self.filtered(lambda l: l.team_id):
            lead.team_lead = lead.team_id.user_id.name

class OpportunityType(models.Model):

    _name = "dms.opportunity.type"
    _description = "Opportunity Type"

    name = fields.Char('Opportunity Type', required=True, index=True)
    description = fields.Char('Description', required=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer('Color')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    team_id = fields.Many2one('crm.team', string='Default Sales Team', required=True)
    categ_id = fields.Many2one('product.category',string="Default category", required=True)
    team_type = fields.Char('Team Type', compute='_get_team_type')

    @api.depends('team_id')
    @api.multi
    def _get_team_type(self):
        for type in self:
            type.team_type = type.team_id.team_type or False
