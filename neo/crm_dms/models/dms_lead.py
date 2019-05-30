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
    color_value = fields.Char(compute='_compute_enquiry_values',string='Color',help ='true')
    variant_value = fields.Char(compute='_compute_enquiry_values',string='Variant',help ='true')
    vehicle_name = fields.Char(compute='_compute_enquiry_values',string='Vehicle',help ='true')
    team_lead = fields.Char(compute='_compute_lead',string = 'Team Lead')
    member_values = fields.One2many('res.users', string='Team',
                                    compute='compute_member_values')
    opportunity_name = fields.Char(compute='_compute_enquiry_values',string='Name',help ='true')

    @api.model
    def _onchange_user_values(self, user_id):
        """ returns new values when user_id has changed """
        if not user_id:
            return {}
        if user_id and self._context.get('team_id'):
            team = self.env['crm.team'].browse(self._context['team_id'])
            if user_id in team.member_ids.ids:
                return {}
            if user_id == team.user_id.id:
                return {'team_id': team.id}
        team_id = self.env['crm.team']._get_default_team_id(user_id=user_id)
        return {'team_id': team_id}

    @api.onchange('team_id')
    def compute_member_values(self):
        self.user_id = False
        team = self.sudo().env['crm.team'].search([('id', '=', self.team_id.id)])
        print("****************************************************************************************")
        member_values = team.mapped('member_ids')
        manager_values = team.mapped('manager_user_ids')
        print(member_values, "___________________________________________________________", manager_values)
        self.member_values = manager_values + member_values + team.user_id
        print(self.team_id.manager_user_ids)


    @api.depends('date_open')
    def _compute_days_open(self):
        """ Compute difference between create date and open date """
        for lead in self.filtered(lambda l: l.date_open and l.create_date):
            date_create = fields.Datetime.from_string(lead.create_date)
            # date_open = fields.Datetime.from_string(lead.date_open)
            lead.days_open = abs((fields.Datetime.now() - date_create).days)

    @api.depends('enquiry_id')
    def _compute_enquiry_values(self):
        """ Compute color """
        for lead in self:
            enq = self.sudo().env['dms.enquiry'].search([('id', '=', lead.enquiry_id.id)])
            lead.color_value = enq.product_color.name
            lead.variant_value = enq.product_variant.name
            lead.vehicle_name = enq.product_id.name
            print("#####################",enq.partner_name)
            lead.partner_name = enq.partner_name
            lead.opportunity_name = lead.opportunity_type.name

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
