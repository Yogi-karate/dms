import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ServiceLeads(models.TransientModel):
    _name = 'dms.service.lead'

    @api.model
    def _process_service_leads(self, company):
        vehicles = self.sudo().env['vehicle'].search([('company_id', '=', company.id), ('state', '=', 'sold')])
        service_type = self.sudo().env['dms.opportunity.type'].search(
            [('name', '=', 'Service'), ('company_id', '=', company.id)])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        for vehicle in vehicles:
            if not vehicle.date_order:
                continue
            service_lead_dict1 = self._create_service_first_leads(vehicle, service_type, today)
            if service_lead_dict1 and not self._check_duplicate(service_lead_dict1):
                leads.append(service_lead_dict1)
            else:
                pass
            service_lead_dict2 = self._create_service_second_leads(vehicle, service_type, today)
            if service_lead_dict2 and not self._check_duplicate(service_lead_dict2):
                leads.append(service_lead_dict2)
            else:
                pass
            service_lead_dict3 = self._create_service_third_leads(vehicle, service_type, today)
            if service_lead_dict3 and not self._check_duplicate(service_lead_dict3):
                leads.append(service_lead_dict3)
            else:
                pass
            service_lead_dict5 = self._create_service_periodic_leads(vehicle, service_type, today)
            if service_lead_dict5 and not self._check_duplicate(service_lead_dict5):
                leads.append(service_lead_dict5)
            else:
                pass
        teams = self.sudo().env['crm.team'].search(
            [('team_type', '=', 'business-center'), ('member_ids', '!=', False), ('company_id', '=', company.id)])
        for lead in leads:
            lead.update({'company_id': company.id})
        self._allocate_user(leads, teams)
        created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))

    @api.model
    def _process_insurance_leads(self, company):
        vehicles = self.sudo().env['vehicle'].search([('company_id', '=', company.id), ('state', '=', 'sold')])
        insurance_type = self.env['dms.opportunity.type'].search(
            [('name', '=ilike', 'Insurance'), ('company_id', '=', company.id)])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        for vehicle in vehicles:
            insurance_lead_dict = self._create_insurance_leads(vehicle, insurance_type, today)
            if insurance_lead_dict and not self._check_duplicate(insurance_lead_dict):
                leads.append(insurance_lead_dict)
            else:
                continue
        self._allocate_insurance_user(leads, company)
        for lead in leads:
            lead.update({'company_id': company.id})
        created_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Insurance Leads for %s", len(created_leads), str(today))

    @api.model
    def _check_duplicate(self, lead_dict):
        dup = self.sudo().env['dms.vehicle.lead'].search([('name', '=', lead_dict['name']),
                                                          ('partner_name', '=', lead_dict['partner_name']),
                                                          ('mobile', '=', lead_dict['mobile']),
                                                          ('date_deadline', '=',
                                                           lead_dict['date_deadline'])])
        if dup:
            return True
        else:
            return False

    @api.model
    def _process_insurance_leads_oct(self):
        vehicles = self.sudo().env['vehicle'].search([('company_id', '=', company.id), ('state', '=', 'sold')])
        insurance_type = self.env['dms.opportunity.type'].search([('name', '=ilike', 'Insurance')])
        today = fields.Datetime.now()
        today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
        leads = []
        for vehicle in vehicles:
            insurance_lead_dict = self._create_october_leads(vehicle, insurance_type, today)
            if insurance_lead_dict:
                leads.append(insurance_lead_dict)
        self._allocate_insurance_user(leads)
        created_leads = self.env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Insurance Leads for %s", len(created_leads), str(today))

    @api.model
    def _process_follow_up(self):
        leads = self.sudo().env['dms.vehicle.lead'].search([('current_due_date', '=', False)], limit=10)
        today = fields.Datetime.now()
        for lead in leads:
            activity_type = self.env['mail.activity.type'].search([('name', 'like', 'Call')], limit=1)
            model_id = self.env['ir.model']._get('dms.vehicle.lead').id
            sample_vals = {
                'res_model_id': 351,
                'res_id': lead.id,
                'date_deadline': '2019-09-14',
                'user_id': 2,
                'activity_category': 'default',
                'force_next': False,
                'previous_activity_type_id': False,
                'recommended_activity_type_id': False,
                'activity_type_id': 8, 'summary': False,
                'note': '<p>HALLLLO</p>'
            }
            _logger.info("Before Create %s Insurance Leads for %s and activity - %s", lead.name, len(leads),
                         len(lead.activity_ids))
            activities = self.env['mail.activity'].with_context(default_res_id=lead.id,
                                                                default_res_model=model_id).create(sample_vals)
            _logger.info("Created %s Insurance Leads for %sand activity - %s", lead.name, len(leads),
                         len(lead.activity_ids))

    @api.model
    def _total_users(self, teams):
        users = []
        for team in teams:
            users = users + team.member_ids.ids
        return users

    @api.model
    def _allocate_insurance_user(self, leads, company):
        self_team = self.sudo().env['crm.team'].search(
            [('team_type', '=', 'business-center-insurance-renewal'), ('user_id', '!=', False),
             ('company_id', '=', company.id)], limit=1)
        other_teams = self.sudo().env['crm.team'].search(
            [('team_type', '=', 'business-center-insurance-rollover'), ('member_ids', '!=', False),
             ('user_id', '!=', False), ('company_id', '=', company.id)])
        self_leads = [lead for lead in leads if lead['source'] == 'saboo']
        other_leads = [lead for lead in leads if lead['source'] != 'saboo']
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
            if team_id not in team_dict.keys():
                team_dict[team_id] = -1
            current_team = teams[team_id]
            members = current_team.member_ids
            user_id = self._round_robin(len(members), team_dict[team_id])
            user = current_team.member_ids[user_id]
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
    def _prepare_leads(self, vehicle, type, date_follow_up, service_type, delta):
        return {
            'name': vehicle.partner_name + '-' + vehicle.product_id.name,
            'partner_name': vehicle.partner_name,
            'mobile': vehicle.partner_mobile,
            'street': vehicle.partner_id.street,
            'opportunity_type': type.id,
            'date_deadline': date_follow_up + timedelta(delta),
            'vehicle_id': vehicle.id,
            'type': 'lead',
            'service_type': service_type,
            'vin_no': vehicle.chassis_no,
            'registration_no': vehicle.registration_no,
            'dos': vehicle.date_order,
            'source': vehicle.source
        }

    @api.model
    def _schedule_follow_up(self, lead, today):
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
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        return dict

    def _create_service_second_leads(self, vehicle, type, today):

        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None
        if today + timedelta(7) == sale_date + timedelta(120) and vehicle.fuel_type == 'diesel':
            service_type = 'second'
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        if today + timedelta(7) == sale_date + timedelta(180) and vehicle.fuel_type == 'petrol':
            service_type = 'second'
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        return dict

    def _create_service_third_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None

        if today + timedelta(7) == sale_date + timedelta(240) and vehicle.fuel_type == 'diesel':
            service_type = 'third'
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        if today + timedelta(7) == sale_date + timedelta(365) and vehicle.fuel_type == 'petrol':
            service_type = 'third'
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        return dict

    def _create_service_periodic_leads(self, vehicle, type, today):
        sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        dict = None
        if (today + timedelta(7) - sale_date).days >= 365 and (
                today + timedelta(7) - sale_date).days % 120 == 0 and vehicle.fuel_type == 'diesel':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        if (today + timedelta(7) - sale_date).days >= 365 and (
                today + timedelta(7) - sale_date).days % 180 == 0 and vehicle.fuel_type == 'petrol':
            service_type = 'paid'
            dict = self._prepare_leads(vehicle, type, today, service_type, 7)
        return dict

    def _create_insurance_leads(self, vehicle, type, today):
        dict = None
        if vehicle.date_order:
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        else:
            return
        if (today + timedelta(90) - sale_date).days % 365 == 0:
            service_type = 'Insurance'
            dict = self._prepare_leads(vehicle, type, today, service_type, 90)
        return dict

    def _create_october_leads(self, vehicle, type, today):
        dict = None
        if vehicle.date_order:
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
        else:
            return
        if sale_date.month == 10 or sale_date.month == 9:
            dat = sale_date.replace(2019, int(sale_date.month), int(sale_date.day), 00, 00, 00, 00)
            delta = (dat - today).days
            service_type = 'Insurance'
            dict = self._prepare_leads(vehicle, type, dat - timedelta(7), service_type, delta)
        return dict

    @api.model
    def _process_lead_due_date(self):
        leads = self.env['dms.vehicle.lead'].search(
            [('current_due_date', '=', False), ('activity_date_deadline', '!=', False)])
        for lead in leads:
            _logger.info("Checking current due date for  %s  Lead  with date %s", lead, lead.current_due_date)
            lead.current_due_date = lead.activity_date_deadline
        _logger.info("Updated current due date for  %s  Leads ", len(leads))

    @api.model
    def create_all_company_service_leads(self, autocommit=True):
        self._clean_service_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of All Company Service Leads!!!!!!!!!!!!!!!!")
        # get All Child Companies
        companies = self.sudo().env['res.company'].search([('parent_id', '!=', False)])
        if companies:
            for company in companies:
                self._process_service_leads(company)
        _logger.info("****************Finished creating All Company Service Leads****************")
        pass

    @api.model
    def create_all_company_insurance_leads(self, autocommit=True):
        # self._clean_service_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of All Company Service Leads!!!!!!!!!!!!!!!!")
        # get All Child Companies
        companies = self.sudo().env['res.company'].search([('parent_id', '!=', False)])
        if companies:
            for company in companies:
                self._process_insurance_leads(company)
        _logger.info("****************Finished creating All Company Service Leads****************")
        pass

    @api.model
    def create_service_leads(self, autocommit=True):
        self._clean_service_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Service Leads!!!!!!!!!!!!!!!!")
        self.create_all_company_service_leads()
        _logger.info("****************Finished creating Service Leads****************")
        pass

    @api.model
    def create_insurance_leads(self, autocommit=True):
        self._clean_insurance_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Insurance Leads!!!!!!!!!!!!!!!!")
        self.create_all_company_insurance_leads()
        _logger.info("****************Finished creating Insurance Leads****************")
        pass

    @api.model
    def create_insurance_leads_oct(self, autocommit=True):
        self._clean_insurance_leads()
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Insurance Leads Oct!!!!!!!!!!!!!!!!")
        self._process_insurance_leads_oct()
        _logger.info("****************Finished creating Insurance Leads oct****************")
        pass

    @api.model
    def update_current_due_date(self, autocommit=True):
        _logger.info("!!!!!!!!!!!!!!Starting Updation of Current Due date!!!!!!!!!!!!!!!!")
        self._process_lead_due_date()
        _logger.info("****************Finished Updation of Current Due date****************")
        pass

    @api.model
    def _clean_insurance_leads(self):
        pass

    @api.model
    def _clean_service_leads(self):
        today = datetime.strptime(datetime.strftime(fields.Datetime.now(), '%Y%m%d'), '%Y%m%d')
        lead_ids = self.env['dms.vehicle.lead'].search([('create_date', '=', today)]).unlink()
        pass

    @api.model
    def create_service_leads_new(self, autocommit=True):
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Service Leads NEW....!!!!!!!!!!!!!!!!")
        schedules = self.env['service.schedule'].search([])
        print("the schedules in the system are ", schedules)
        schedules.generate_leads()
        _logger.info("****************Finished creating Service Leads NEW ....****************")
        pass

    @api.model
    def create_insurance_leads_new(self, autocommit=True):
        _logger.info("!!!!!!!!!!!!!!Starting Creation of Service Leads NEW....!!!!!!!!!!!!!!!!")
        schedules = self.env['insurance.schedule'].search([])
        print("the schedules in the system are ", schedules)
        schedules.generate_leads()
        _logger.info("****************Finished creating Service Leads NEW ....****************")
        pass
