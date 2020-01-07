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

    @api.onchange('schedule_type')
    def _clear(self):
        self.min_days = False
        self.max_days = False
        self.days = False

    @api.multi
    def generate_leads(self):
        for schedule in self:
            schedule._generate_leads()

    @api.model
    def _generate_leads(self):
        if self.product_category_id:
            products = self.sudo().env['product.template'].with_context(active_test=False).search(
                [('categ_id', '=', self.product_category_id.id)])
            prods = self.sudo().env['product.product']
            if self.product_type == 'na':
                prods = prods.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids)])
            else:
                prods = prods.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids), ('fuel_type', '=', self.product_type)])
            vehicles = self.sudo().env['vehicle'].with_context(active_test=False).search(
                [('product_id', 'in', prods.ids), ('state', '=', 'sold'),
                 ('date_order', '!=', False)])
            print("%%%%% the vehicles", len(vehicles))
        elif self.product_temp_id:
            products = self.sudo().env['product.template'].with_context(active_test=False).search(
                [('id', '=', self.product_temp_id.id)])
            prods = self.sudo().env['product.product']
            if self.product_type == 'na':
                prods = prods.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids)])
            else:
                prods = prods.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids),
                     ('fule_type', '=', self.product_type)])

            vehicles = self.sudo().env['vehicle'].with_context(active_test=False).search(
                [('product_id', 'in', prods.ids), ('state', '=', 'sold'),
                 ('date_order', '!=', False)])
        else:
            vehicles = self.sudo().env['vehicle'].search([('product_id', '=', self.product_id.id)])
        leads = []
        for vehicle in vehicles:
            today = fields.Datetime.now().date()
            today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
            diff = (today - sale_date).days
            if not self.days:
                if not self.max_days:
                    if diff > self.min_days:
                        dict = self._prepare_leads(vehicle, today, self.service_type, self.delta)
                        leads.append(dict)
                else:
                    if diff > self.min_days and diff < self.max_days:
                        dict = self._prepare_leads(vehicle, today, self.service_type, self.delta)
                        leads.append(dict)
            else:
                if diff % self.days == 0:
                    dict = self._prepare_leads(vehicle, today, self.service_type, self.delta)
                    leads.append(dict)
            if self.allocation_type == 'Round-Robin':
                teams = self.sudo().env['crm.team'].search(
                    [('team_type', '=', self.team_type), ('member_ids', '!=', False),
                     ('company_id', '=', self.company.id)])
                self._allocate_user(leads, teams)
            elif self.allocation_type == 'Lead':
                for lead in leads:
                    lead.update({'user_id': self.team_id.user_id.id})
            elif self.allocation_type == 'user':
                for lead in leads:
                    lead.update({'user_id': self.user_id.id})

        for lead in leads:
            lead.update({'company_id': self.company.id})

        created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))



