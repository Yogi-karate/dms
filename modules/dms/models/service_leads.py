import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ServiceLeads(models.TransientModel):
    _name = 'dms.service.lead'

    @api.model
    def _process(self):
       # vehicles = self.env['vehicle'].search([('ref', 'ilike', '2412')])
        vehicles = self.env['vehicle'].search([])
        service_type = self.env['dms.opportunity.type'].search([('name', '=', 'Service')])
        insurance_type = self.env['dms.opportunity.type'].search([('name', '=', 'Insurance')])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        insurance_leads = []
        # if len(teams) == 0:
        #     print("-------Cannot execute as no teams to allocate leads---------")
        #     return
        # users = self._total_users(teams)
        # user_value = -1
        # user_length = len(users)
        # print("the number of users", user_length)
        for vehicle in vehicles:
            print("The vehicle in service lead generation", vehicle)
            # user_value = self._round_robin(user_length, user_value)
            # print("---the team chosen---", user_value)
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
            insurance_lead_dict = self._create_insurance_leads(vehicle, insurance_type, today)
            if insurance_lead_dict:
                insurance_leads.append(insurance_lead_dict)
        created_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead,today)
        self._allocate_user(created_leads)
        created_insurance_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(insurance_leads)
        for lead in created_insurance_leads:
            self._schedule_follow_up(lead, today)
        self._allocate_insurance_user(created_insurance_leads)
        print("The created leads are ", created_leads)

    @api.model
    def _total_users(self, teams):
        users = []
        for team in teams:
            users = users + team.member_ids.ids
        print("the total number of call center users", users)
        return users

    @api.model
    def _allocate_user(self, leads):
        teams = self.sudo().env['crm.team'].search([('team_type', '=', 'business-center')])
        # print(len(teams),"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        team_dict = {}
        previous_team_id = -1
        for lead in leads:
            team_id = self._round_robin(len(teams),previous_team_id)
            if not team_dict.get(team_id,False):
                # print("team dict checking","___________________________",team_id)
                team_dict[team_id] = -1
            current_team = teams[team_id]
            members = current_team.member_ids
            for x in members:
                print(x.name,x)
            user_id = self._round_robin(len(members),team_dict[team_id])
            # print(user_id,"________________________________________________",team_dict)
            user = current_team.member_ids[user_id]
            # print(user,":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::",user.name)
            # update team_dict with new value
            team_dict[team_id] = user_id
            # update the lead with this user_id
            lead.write({
                    'user_id': user.id,
                    'team_id': current_team.id})
            previous_team_id = team_id

    @api.model
    def _allocate_insurance_user(self, leads):
        teams = self.sudo().env['crm.team'].search([('team_type', '=', 'insurance'),('member_ids','!=',False)])
        print(teams,"___________________________________________________________team___team____team")
        #teams = self.sudo().env['crm.team'].search([('id', '=',199)])
        for team in teams:
            print(team,"::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            for x in team.member_ids:
                print(x,">>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        # print(len(teams),"<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        team_dict = {}
        previous_team_id = -1
        for lead in leads:
            team_id = self._round_robin(len(teams), previous_team_id)
            if not team_dict.get(team_id, False):
                # print("team dict checking","___________________________",team_id)
                team_dict[team_id] = -1
            current_team = teams[team_id]
            members = current_team.member_ids
            for x in members:
                print(x.name, x)
            user_id = self._round_robin(len(members), team_dict[team_id])
            print(user_id,"________________________________________________",team_dict)
            user = current_team.member_ids[user_id]
            print(user,":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
            # update team_dict with new value
            team_dict[team_id] = user_id
            # update the lead with this user_id
            lead.write({
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
    def _prepare_leads(self, vehicle, type, date_follow_up,service_type):
        print("typeeeepeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",type)
        # customer = self._create_lead_partner()
        return {
            'name': vehicle.partner_name + '-' + vehicle.product_id.name,
            'partner_name': vehicle.partner_name,
            'mobile': vehicle.partner_mobile,
            'opportunity_type': type.id,
            'date_deadline': date_follow_up,
            'vehicle_id': [(6, 0, [vehicle.id])],
            'type':'lead',
            'service_type':service_type
        }

    @api.model
    def _schedule_follow_up(self, lead,today):

        print(lead,"ggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg")
        lead.activity_schedule(
            'crm_dms.mail_activity_data_follow_up',
            user_id=lead.user_id.id,
            note=_(
                "Follow up  on  <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer %s") % (
                     lead._name, lead.id, lead.name,
                     lead.partner_name),
            date_deadline=today + timedelta(2))

    def _create_service_first_leads(self, vehicle, type, today):
        # print("Vehicle Sale Date", vehicle.order_date)
        # print("Hello Today", today)
        # rec_date_from = today + timedelta(30)
        # print("TimeDelta Value - ", rec_date_from)
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        # print(sale_date,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        # print(today,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        dict = None
        print(today - timedelta(11))
        if today + timedelta(9) == sale_date + timedelta(20):
            service_type = 'first'
            dict = self._prepare_leads(vehicle, type, today,service_type)
        # self._schedule_follow_up(lead)
        return dict
        return
    def _create_service_second_leads(self, vehicle, type, today):
        # print("Vehicle Sale Date", vehicle.order_date)
        # print("Hello Today", today)
        # rec_date_from = today + timedelta(30)
        # print("TimeDelta Value - ", rec_date_from)
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        # print(sale_date,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        # print(today,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        dict = None
        # print(today - timedelta(11))
        print(today + timedelta(9) == sale_date + timedelta(140),"PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")
        if today + timedelta(9) == sale_date + timedelta(140) and vehicle.fuel_type == 'diesel':
            print(dict,":::::::::::::::::::::::::::::::::::::::::::::::::::::::condition checked")
            service_type = 'second'
            dict = self._prepare_leads(vehicle, type, today,service_type)
            print(dict,":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::dict here")
        if today + timedelta(9) == sale_date + timedelta(200) and vehicle.fuel_type == 'petrol':
            service_type = 'second'
            dict = self._prepare_leads(vehicle, type, today, service_type)
        # self._schedule_follow_up(lead)
        return dict
        return
    def _create_service_third_leads(self, vehicle, type, today):
        # print("Vehicle Sale Date", vehicle.order_date)
        # print("Hello Today", today)
        # rec_date_from = today + timedelta(30)
        # print("TimeDelta Value - ", rec_date_from)
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        # print(sale_date,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        # print(today,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        dict = None
        print(today - timedelta(11))
        if today + timedelta(9) == sale_date + timedelta(260) and vehicle.fuel_type == 'diesel':
            service_type = 'third'
            dict = self._prepare_leads(vehicle, type, today,service_type)
        if today + timedelta(9) == sale_date + timedelta(320) and vehicle.fuel_type == 'petrol':
            service_type = 'third'
            dict = self._prepare_leads(vehicle, type, today, service_type)
        # self._schedule_follow_up(lead)
        return dict
        return
    def _create_service_paid_leads(self, vehicle, type, today):
        print("Vehicle Sale Date", vehicle.order_date)
        print("Hello Today", today)
        # rec_date_from = today + timedelta(30)
        # print("TimeDelta Value - ", rec_date_from)
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        # print(sale_date,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        # print(today,"{{{{{{{{{{{{{{{{{{{}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}")
        dict = None
        print(today - timedelta(11))
        if today + timedelta(9) == sale_date + timedelta(365) and vehicle.fuel_type == 'diesel':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today,service_type)
        if today + timedelta(9) == sale_date + timedelta(425) and vehicle.fuel_type == 'petrol':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type)
        # self._schedule_follow_up(lead)
        return dict
        return


    def _create_insurance_leads(self, vehicle, type, today):
        dict = None
        print("insuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsuranceinsurance")
        sale_date = datetime.strptime(vehicle.order_date, '%d-%b-%Y')
        rec_date_from = today - sale_date
        print("TimeDelta Value - ", rec_date_from)
        print("TimeDelta Value 120 days- ", rec_date_from.days % 120)
        if today + timedelta(9) == sale_date + timedelta(365):
            service_type = 'Insurance'
            dict = self._prepare_leads(vehicle, type, today, service_type)
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
