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
    _inherit = 'vehicle.schedule'

    service_type = fields.Many2one('service.type')
    min_distance = fields.Integer('Kilometers Run(Min)')
    max_distance = fields.Integer('Kilometers Run(Max)')
    min_days = fields.Integer('Minimum Days', required=True)
    max_days = fields.Integer('Maximum Days')

    @api.onchange('product_radio')
    def _clear_product(self):
        self.product_temp_id = False
        self.product_id = False
        self.product_category_id = False

    @api.onchange('schedule_type')
    def _clear_type(self):
        self.min_days = False
        self.max_days = False
        self.days = False

    @api.model
    def generate_service_leads(self, cr, uid, context=None):
        self = self.env['service.schedule'].search([('id', '=', cr[0])])
        self._generate_leads()
        print("======================================================================================", self)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    @api.model
    def _prepare_leads(self, vehicle, date_follow_up, service_type, delta):
        lead = super(ServiceSchedule, self).prepare_leads(vehicle, date_follow_up, delta)
        lead.update({'service_type': service_type.id})
        return lead

    @api.model
    def _generate_leads(self):
        print("=========================================--------------------------",self)
        leads = []
        if not self.particular_day:
            today = fields.Datetime.now().date()
        else:
            today = self.particular_day.date()
        for vehicle in self._get_vehicles_for_schedule(None, None):
            lead = {}
            today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
            diff = (today - sale_date).days
            if not self.days:
                if not self.max_days:
                    if diff == self.min_days:
                        lead = self._prepare_leads(vehicle, today, self.service_type, self.delta)
                else:
                    if diff > self.min_days and diff < self.max_days:
                        lead = self._prepare_leads(vehicle, today, self.service_type, self.delta)
            else:
                if diff % self.days == 0:
                    lead = self._prepare_leads(vehicle, today, self.service_type, self.delta)
            if lead and not self.check_duplicate(lead):
                leads.append(lead)
        print("The leads generated are &&&&&&&&&&&&&&&&&", leads)
        if leads:
            created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(
                self.allocate_users_for_schedule(leads))
            for lead in created_leads:
                self._schedule_follow_up(lead, today)
            _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))
        else:
            _logger.info("No Service Leads for %s", str(today))
        return 
