import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ServiceLeads(models.TransientModel):
    _name = 'dms.service.lead'

    @api.model
    def _process(self):
        vehicles = self.env['vehicle'].search([('ref', 'ilike', '2412')])
        teams = self.env['crm.team'].search([('team_type', '=', 'business-center')])
        service_type = self.env['dms.opportunity.type'].search([('name', '=', 'Service')])
        insurance_type = self.env['dms.opportunity.type'].search([('name', '=', 'Insurance')])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        if len(teams) == 0:
            print("-------Cannot execute as no teams to allocate leads---------")
            return
        users = self._total_users(teams)
        user_value = -1
        user_length = len(users)
        print("the number of users", user_length)
        for vehicle in vehicles:
            print("The vehicle in service lead generation", vehicle)
            user_value = self._round_robin(user_length, user_value)
            print("---the team chosen---", user_value)
            service_lead_dict = self._create_service_leads(vehicle, users[user_value], service_type, today)
            if service_lead_dict:
                leads.append(service_lead_dict)
            insurance_lead_dict = self._create_insurance_leads(vehicle, users[user_value], insurance_type, today)
            # if insurance_lead_dict:
            #     leads.append(insurance_lead_dict)
            created_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
            print("The created leads are ", created_leads)

    @api.model
    def _total_users(self, teams):
        users = []
        for team in teams:
            users = users + team.member_ids.ids
        print("the total number of call center users", users)
        return users

    @api.model
    def _allocate_user(self, dict, team_dict):


    @api.model
    def _round_robin(self, length, value):
        if value == length - 1 or value == -1:
            return 0
        elif value < length - 1:
            return value + 1

    @api.model
    def _prepare_leads(self, vehicle, user_id, type, date_follow_up):
        # customer = self._create_lead_partner()
        return {
            'name': vehicle.partner_name + '-' + vehicle.product_id.name,
            'partner_name': vehicle.partner_name,
            'mobile': vehicle.partner_mobile,
            'opportunity_type': type.id,
            'date_deadline': date_follow_up,
            'vehicle_id': [(6, 0, [vehicle.id])]
        }

    @api.model
    def _schedule_follow_up(self, lead):
        lead.activity_schedule(
            'crm_dms.mail_activity_data_follow_up',
            user_id=lead.user_id.id,
            note=_(
                "Follow up  on  <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer %s") % (
                     lead._name, lead.id, lead.name,
                     lead.partner_name),
            date_deadline=lead.date_deadline)

    def _create_service_leads(self, vehicle, user_id, type, today):
        print("Vehicle Sale Date", vehicle.order_date)
        print("Hello Today", today)
        rec_date_from = today + timedelta(30)
        print("TimeDelta Value - ", rec_date_from)
        dict = self._prepare_leads(vehicle, user_id, type, today)
        # self._schedule_follow_up(lead)
        return dict

    def _create_insurance_leads(self, vehicle, user_id, type, today):
        sale_date = datetime.strptime(vehicle.order_date, '%d-%b-%Y')
        rec_date_from = today - sale_date
        print("TimeDelta Value - ", rec_date_from)
        print("TimeDelta Value 120 days- ", rec_date_from.days % 120)
        dict = self._prepare_leads(vehicle, user_id, type, today)
        # self._schedule_follow_up(lead)
        return dict

    @api.model
    def _create_leads(self, autocommit=True):
        self._clean_service_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Service Leads!!!!!!!!!!!!!!!!")
        self._process()
        _logger.info("****************Finished creating Service Leads****************")
        pass

    @api.model
    def _clean_service_leads(self):
        pass
