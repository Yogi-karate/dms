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

    @api.depends('date_open')
    def _compute_days_open(self):
        """ Compute difference between create date and open date """
        for lead in self.filtered(lambda l: l.date_open and l.create_date):
            date_create = fields.Datetime.from_string(lead.create_date)
            # date_open = fields.Datetime.from_string(lead.date_open)
            lead.days_open = abs((fields.Datetime.now() - date_create).days)


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
