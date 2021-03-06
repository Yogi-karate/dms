# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class ActivityDoneReport(models.Model):
    """ CRM Lead Analysis """

    _name = "crm.activity.done.report"
    _auto = False
    _description = "DMS Vehicle Lead Activity Analysis"
    _rec_name = 'id'

    date = fields.Datetime('Date', readonly=True)
    author_id = fields.Many2one('res.partner', 'Created By', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
    lead_id = fields.Many2one('crm.lead', "Lead", readonly=True)
    subject = fields.Char('Summary', readonly=True)
    subtype_id = fields.Many2one('mail.message.subtype', 'Subtype', readonly=True)
    mail_activity_type_id = fields.Many2one('mail.activity.type', 'Activity Type', readonly=True)
    country_id = fields.Many2one('res.country', 'Country', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    stage_id = fields.Many2one('crm.stage', 'Stage', readonly=True)
    partner_name = fields.Char('Customer', readonly=True)
    mobile = fields.Char('Mobile', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner/Customer', readonly=True)
    lead_type = fields.Char(
        string='Type',
        selection=[('lead', 'Lead'), ('opportunity', 'Opportunity')],
        help="Type is used to separate Leads and Opportunities")
    active = fields.Boolean('Active', readonly=True)
    probability = fields.Float('Probability', group_operator='avg', readonly=True)
    summary = fields.Char(
        'Next Activity Summary', )
    call_type = fields.Char('Type')
    opportunity_type = fields.Many2one('dms.opportunity.type', 'Opportunity Type', readonly=True)
    disposition = fields.Many2one('dms.lead.disposition', string="Disposition")
    registration_no = fields.Char('Registration')
    vehicle_id = fields.Many2one('vehicle',string='VIN No')
    def _select(self):
        return """
            SELECT
                m.id,
                m.subtype_id,
                m.mail_activity_type_id,
                m.author_id,
                m.body as summary,
                m.date,
                m.subject,
                l.id as lead_id,
                l.partner_name as partner_name,
                l.mobile as mobile,
                l.user_id,
                l.team_id,
                l.country_id,
                l.company_id,
                l.stage_id,
                l.partner_id,
                l.type as lead_type,
                l.active,
                l.call_type,
                l.probability,
                l.opportunity_type,
                l.disposition,
                l.registration_no as registration_no,
                l.vehicle_id as vehicle_id
        """

    def _from(self):
        return """
            FROM mail_message AS m
        """

    def _join(self):
        return """
            JOIN dms_vehicle_lead AS l ON m.res_id = l.id
        """

    def _where(self):
        return """
            WHERE
                m.model = 'dms.vehicle.lead' AND m.mail_activity_type_id IS NOT NULL
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where())
                         )
