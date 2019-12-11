import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ServiceType(models.Model):
    _name = 'service.type'
    name = fields.Char('name')
    paid = fields.Boolean('paid')

class ServiceHistory(models.Model):
    _name = 'service.history'
    type = fields.Many2one('service.type')
    vehicle = fields.Many2one('vehicle')
    service_date = fields.Date('Service Date')
    service_km = fields.Integer('Kilometers Run')

class ServiceSchedule(models.Model):
    _name = 'service.schedule'
    name = fields.Char(
        'Schedule', required=True, help="Unique Vehicle Chassis Number")
    type = fields.Many2one('service.type')
    product_temp_id = fields.Many2one('product.template')
    product_id = fields.Many2one('product.product')
    parent_id = fields.Many2one('service.schedule')
    min_distance = fields.Integer('Kilometers Run(Min)')
    max_distance = fields.Integer('Kilometers Run(Max)')
    min_days = fields.Integer('Minimum Days', required=True)
    max_days = fields.Integer('Maximum Days')
    delta = fields.Integer('Days for followup')
    company = fields.Many2one('res.company')
    active = fields.Boolean('active', default = True)

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

    def _generate_leads(self):
        vehicles = self.sudo().env['vehicle'].search([('product_id','=',self.product_id.id)])
        leads = []
        for vehicle in vehicles:
            today = fields.Datetime.now()
            today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
            diff = (today - sale_date).days
            if not self.max_days:
                if diff > self.min_days:
                    dict = self._prepare_leads(vehicle,self.type.name,today,self.type.name,self.delta)
                    leads.append(dict)
                    
            else:
                if diff  > self.min_days and diff < self.max_days:
                    dict = self._prepare_leads(vehicle, self.type.name, today, self.type.name, self.delta)
                    leads.append(dict)

            teams = self.sudo().env['crm.team'].search(
                [('team_type', '=', 'business-center'), ('member_ids', '!=', False), ('company_id', '=', self.company.id)])
            for lead in leads:
                lead.update({'company_id': self.company.id})
            self._allocate_user(leads, teams)
            created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
            for lead in created_leads:
                self._schedule_follow_up(lead, today)
            _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))


