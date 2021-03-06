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
    def generate_leads(self,cr,uid,context=None):
        self = self.env['insurance.schedule'].search([('id','=',cr[0])])
        self._generate_leads()
        print("======================================================================================",self)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    @api.model
    def _generate_leads(self):
        if not self.particular_day:
            today = fields.Datetime.now().date()
        else:
            today = self.particular_day.date()
        leads = []
        for vehicle in self._get_vehicles_for_schedule([],[('source','=',self.source)]):
            lead = {}
            today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
            diff = (today + timedelta(self.offset_days) - sale_date).days
            if diff % self.days == 0:
                lead = self.prepare_leads(vehicle, today, self.delta)
            if lead and not self.check_duplicate(lead):
                leads.append(lead)
        created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(
            self.allocate_users_for_schedule(leads))
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))
        return
