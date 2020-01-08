import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class InsuranceSchedule(models.Model):
    _name = 'insurance.schedule'
    _inherit = 'vehicle.schedule'

    source = fields.Selection([
        ('od', 'Other Dealer'),
        ('saboo', 'Saboo'),
    ], string='Source', store=True, default='saboo')

    @api.onchange('schedule_type')
    def _clear_type(self):
        self.days = False

    @api.onchange('product_radio')
    def _clear_product(self):
        self.product_temp_id = False
        self.product_id = False
        self.product_category_id = False

    @api.model
    def _generate_leads(self):

        leads = []
        for vehicle in self._get_vehicles_for_schedule():
            today = fields.Datetime.now().date()
            today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
            diff = (today - sale_date).days
            if diff % self.days == 0:
                dict = self._prepare_leads(vehicle, today, self.delta)
                leads.append(dict)

        created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(
            self.allocate_users_for_schedule(leads))
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))
