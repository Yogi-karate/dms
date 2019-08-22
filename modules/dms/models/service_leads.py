import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ServiceLeads(models.TransientModel):
    _name = 'dms.service.lead'

    @api.model
    def _process_service_leads(self):
        # vehicles = self.env['vehicle'].search([('ref', 'ilike', '2412')])
        vehicles = self.env['vehicle'].search([],limit=100)
        service_type = self.env['dms.opportunity.type'].search([('name', '=', 'Service')])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        for vehicle in vehicles:
            if not vehicle.date_order:
                continue
            print("The vehicle in service lead generation", vehicle)
            service_lead_dict1 = self._create_service_first_leads(vehicle, service_type, today)
            if service_lead_dict1:
                leads.append(service_lead_dict1)
            service_lead_dict2 = self._create_service_second_leads(vehicle, service_type, today)
            if service_lead_dict2:
                leads.append(service_lead_dict2)
            service_lead_dict3 = self._create_service_third_leads(vehicle, service_type, today)
            if service_lead_dict3:
                leads.append(service_lead_dict3)
            service_lead_dict4 = self._create_service_paid_leads(vehicle, service_type, today)
            if service_lead_dict4:
                leads.append(service_lead_dict4)
            service_lead_dict5 = self._create_service_periodic_leads(vehicle, service_type, today)
            if service_lead_dict5:
                leads.append(service_lead_dict5)
        teams = self.sudo().env['crm.team'].search([('team_type', '=', 'business-center'), ('member_ids', '!=', False)])
        self._allocate_user(leads, teams)
        created_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)

    @api.model
    def _process_insurance_leads(self):
        # vehicles = self.env['vehicle'].search([('ref', 'ilike', '2412')])
        vehicles = self.env['vehicle'].search([],limit=200)
        insurance_type = self.env['dms.opportunity.type'].search([('name', '=ilike', 'Insurance')])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        for vehicle in vehicles:
            print("The vehicle in service lead generation", vehicle)
            insurance_lead_dict = self._create_insurance_leads(vehicle, insurance_type, today)
            if insurance_lead_dict:
                leads.append(insurance_lead_dict)
        created_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        self._allocate_insurance_user(created_leads)
        print("The created leads are ", created_leads)

    @api.model
    def _total_users(self, teams):
        users = []
        for team in teams:
            users = users + team.member_ids.ids
        print("the total number of call center users", users)
        return users

    @api.model
    def _allocate_insurance_user(self, leads):
        self_team = self.sudo().env['crm.team'].search(
            [('team_type', '=', 'business-center-insurance-renewal'), ('user_id', '!=', False)], limit=1)
        other_teams = self.sudo().env['crm.team'].search(
            [('team_type', '=', 'business-center-insurance-rollover'), ('member_ids', '!=', False), ('user_id', '!=', False)])
        self_leads = leads.filtered(lambda l: l.source == 'saboo')
        other_leads = leads.filtered(lambda l: not l.source == 'saboo')
        print(self_leads,"----------------------------------------self leads")
        print(other_leads,"---------------------------------------------------other leads")
        for lead in self_leads:
            lead.update({
                'user_id': self_team.user_id.id,
                'team_id': self_team.id})
        self._allocate_user(other_leads, other_teams)

    @api.model
    def _allocate_user(self, leads, teams):
        team_dict = {}
        previous_team_id = -1
        for lead in leads:
            team_id = self._round_robin(len(teams), previous_team_id)
            print("team dict checking before ", "___________________________", team_dict)
            if team_id not in team_dict.keys():
                print("team dict checking", "___________________________", team_id)
                team_dict[team_id] = -1
            current_team = teams[team_id]
            members = current_team.member_ids
            for x in members:
                print(x.name, x)
            user_id = self._round_robin(len(members), team_dict[team_id])
            print("user id in allocation ---------", user_id)
            user = current_team.member_ids[user_id]
            print("user name in allocation $$$$$$$$$$", user.name)
            team_dict[team_id] = user_id
            lead.update({
                'user_id': user.id,
                'team_id': current_team.id})
            previous_team_id = team_id

    @api.model
    def _round_robin(self, length, value):
        if value == length - 1 or value == -1:
            return 0
        elif value < length - 1:
            return value + 1

    @api.model
    def _prepare_leads(self, vehicle, type, date_follow_up, service_type, call_type, delta):
        print("typeeeepeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", type)
        # customer = self._create_lead_partner()
        return {
            'name': vehicle.partner_name + '-' + vehicle.product_id.name,
            'partner_name': vehicle.partner_name,
            'mobile': vehicle.partner_mobile,
            'opportunity_type': type.id,
            'date_deadline': date_follow_up + timedelta(delta),
            'vehicle_id': [(6, 0, [vehicle.id])],
            'type': 'lead',
            'service_type': service_type,
            'vin_no': vehicle.chassis_no,
            'registration_no': vehicle.registration_no,
            'dos': vehicle.date_order,
            'call_type': call_type
        }

    @api.model
    def _schedule_follow_up(self, lead, today):
        print(lead, "ggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg")
        lead.activity_schedule(
            'mail.mail_activity_data_call',
            user_id=lead.user_id.id,
            note=_(
                "Follow up  on  <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer %s") % (
                     lead._name, lead.id, lead.name,
                     lead.partner_name),
            date_deadline=today + timedelta(2))

    def _create_service_first_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None

        if today + timedelta(7) == sale_date + timedelta(20):
            service_type = 'first'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        return dict

    def _create_service_second_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None
        if today + timedelta(7) == sale_date + timedelta(120) and vehicle.fuel_type == 'diesel':
            print(dict, ":::::::::::::::::::::::::::::::::::::::::::::::::::::::condition checked")
            service_type = 'second'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
            print(dict, ":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::dict here")
        if today + timedelta(7) == sale_date + timedelta(180) and vehicle.fuel_type == 'petrol':
            service_type = 'second'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        return dict

    def _create_service_third_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None

        if today + timedelta(7) == sale_date + timedelta(240) and vehicle.fuel_type == 'diesel':
            service_type = 'third'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        if today + timedelta(7) == sale_date + timedelta(365) and vehicle.fuel_type == 'petrol':
            service_type = 'third'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        return dict

    def _create_service_paid_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None
        if today + timedelta(7) == sale_date + timedelta(365) and vehicle.fuel_type == 'diesel':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        if today + timedelta(7) == sale_date + timedelta(445) and vehicle.fuel_type == 'petrol':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        return dict

    def _create_service_periodic_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None
        print((today + timedelta(7) - sale_date).days % 120,
              ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        if (today + timedelta(7) - sale_date).days > 365 and (
                today + timedelta(7) - sale_date).days % 120 == 0 and vehicle.fuel_type == 'diesel':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        if (today + timedelta(7) - sale_date).days > 445 and (
                today + timedelta(7) - sale_date).days % 180 == 0 and vehicle.fuel_type == 'petrol':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Service', 7)
        return dict

    def _create_insurance_leads(self, vehicle, type, today):
        dict = None
        print("insuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsurance")
        if vehicle.date_order:
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        else:
            return
        # sale_date = datetime.strptime(vehicle.date_order, '%d-%b-%Y')
        rec_date_from = today - sale_date
        print("sale date--------------------------------------------------is--------- ", sale_date)
        print("today is------------------------------------------------------------ ", today)
        print("time delta---------------------------------------------------------------delta--", today + timedelta(90))
        if (today + timedelta(90) - sale_date).days % 365 == 0:
            service_type = 'Insurance'
            dict = self._prepare_leads(vehicle, type, today, service_type, 'Insurance', 90)
        return dict

    @api.model
    def create_service_leads(self, autocommit=True):
        self._clean_service_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Service Leads!!!!!!!!!!!!!!!!")
        self._process_service_leads()
        _logger.info("****************Finished creating Service Leads****************")
        pass

    @api.model
    def create_insurance_leads(self, autocommit=True):
        self._clean_insurance_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Insurance Leads!!!!!!!!!!!!!!!!")
        self._process_insurance_leads()
        _logger.info("****************Finished creating Insurance Leads****************")
        pass

    # @api.model
    # def create_insurance_leads(self, autocommit=True):
    #     self._clean_insurance_leads()
    #     _logger.info("!!!!!!!!!!!!!!Starting Creation of Insurance Leads!!!!!!!!!!!!!!!!")
    #     # self._process_insurance_leads()
    #     _logger.info("****************Finished creating Insurance Leads****************")
    #     pass

    @api.model
    def _clean_insurance_leads(self):
        pass

    @api.model
    def _clean_service_leads(self):
        today = datetime.strptime(datetime.strftime(fields.Datetime.now(), '%Y%m%d'), '%Y%m%d')
        lead_ids = self.env['dms.vehicle.lead'].search([('create_date', '=', today)]).unlink()
        pass
