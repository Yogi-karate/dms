import logging
from odoo import api, fields, tools, models

from datetime import timedelta
_logger = logging.getLogger(__name__)


class DailyLeads(models.TransientModel):
    _name = 'daily.lead.export'

    @api.model
    def export_action(self):
        teams = self.env['crm.team'].search([])
        days = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        for team in teams:
            # print("##################")
            # print(team)
            users = team.member_ids
            for user in users:
                print(user)
                today = fields.Datetime.now()
                for day in range(20):
                    #   print(":::::::::--------")
                    # print(day)
                    rec_date_from = today - timedelta(day)
                    rec_date_to = rec_date_from + timedelta(1)
                    print(":::::::::")
                    print(rec_date_from)
                    print(rec_date_to)
                    leads = self.env['crm.lead'].search(
                        [('create_date', '>', str(rec_date_from)), ('create_date', '<', str(rec_date_to)),
                         ('user_id', '=', user.id)])
                    print("********************************")
                    for x in leads:
                        print(x.id, x.name, "^^^^^^^^^")
                    count = len(leads.ids)
                    dict = {
                        'user_id': user.id,
                        'created_on': rec_date_from,
                        'team_id': team.name,
                        'team_lead': team.user_id.name,
                        'count_opportunities': count
                    }
                    #      print(dict)
                    self.env['user.leads'].create(dict)

    @api.model
    def _process_user_leads(self, autocommit=True):
        self._clean_user_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of User report for Enquiries!!!!!!!!!!!!!!!!")
        self.export_action()
        _logger.info("****************Finished creating user lead report****************")
        pass


    @api.model
    def _clean_user_leads(self):
        domain = []
        self.env['user.leads'].search(domain).unlink()


class UserLeads(models.TransientModel):
    _name = 'user.leads'
    user_id = fields.Many2one('res.users', string="User")
    created_on = fields.Date(string='Create Date')
    count_opportunities = fields.Integer(string="Count")
    name = fields.Char(string='name', compute='_get_name', store=True)
    team_id = fields.Char(string='Team')
    team_lead = fields.Char(string='Team Lead')

    def _get_name(self):
        for ulead in self:
            return ulead.user.name
