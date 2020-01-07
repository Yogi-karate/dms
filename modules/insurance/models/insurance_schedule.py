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
    def _clear(self):
        self.days = False

    @api.onchange('product_radio')
    def _clear(self):
        self.product_temp_id = False
        self.product_id = False
        self.product_category_id = False

    @api.model
    def _prepare_leads(self, vehicle, date_follow_up, delta):
        return {
            'name': vehicle.partner_name + '-' + vehicle.product_id.name,
            'partner_name': vehicle.partner_name,
            'mobile': vehicle.partner_mobile,
            'street': vehicle.partner_id.street,
            'opportunity_type': self.opportunity_type.id,
            'date_deadline': date_follow_up + timedelta(delta),
            'vehicle_id': vehicle.id,
            'type': 'lead',
            'service_type':None,
            'vin_no': vehicle.chassis_no,
            'registration_no': vehicle.registration_no,
            'dos': vehicle.date_order,
            'source': vehicle.source
        }

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
                [('product_id', 'in', prods.ids), ('state', '=', 'sold'), ('source', '=', self.source),
                 ('date_order', '!=', False)])
            print("%%%%% the vehicles", len(vehicles))
        elif self.product_temp_id:
            products = self.sudo().env['product.template'].with_context(active_test=False).search(
                [('name', '=', self.product_temp_id.name)])
            prods = self.sudo().env['product.product']
            if self.product_type == 'na':
                prods = prods.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids)])
            else:
                prods = prods.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids),
                     ('fuel_type', '=', self.product_type)])

            vehicles = self.sudo().env['vehicle'].with_context(active_test=False).search(
                [('product_id', 'in', prods.ids), ('state', '=', 'sold'), ('source', '=', self.source),
                 ('date_order', '!=', False)])
        else:
            vehicles = self.sudo().env['vehicle'].search(
                [('product_id', '=', self.product_id.id)('source', '=', self.source), ])
        leads = []
        for vehicle in vehicles:
            today = fields.Datetime.now().date()
            today = datetime.strptime(datetime.strftime(today, '%Y%m%d'), '%Y%m%d')
            sale_date = datetime.strptime(datetime.strftime(vehicle.date_order, '%Y%m%d'), '%Y%m%d')
            diff = (today - sale_date).days
            if diff % self.days == 0:
                dict = self._prepare_leads(vehicle,today, self.delta)
                leads.append(dict)
            if self.allocation_type == 'Round-Robin':
                teams = self.sudo().env['crm.team'].search(
                    [('team_type', '=', self.team_type), ('member_ids', '!=', False),
                     ('company_id', '=', self.company_id.id)])
                self._allocate_user(leads, teams)
            elif self.allocation_type == 'Lead':
                for lead in leads:
                    lead.update({'user_id': self.team_id.user_id.id})
            elif self.allocation_type == 'user':
                for lead in leads:
                    lead.update({'user_id': self.user_id.id})

        for lead in leads:
            print(lead)
            lead.update({'company_id': self.company_id.id})

        created_leads = self.sudo().env['dms.vehicle.lead'].with_context(mail_create_nosubscribe=True).create(leads)
        for lead in created_leads:
            self._schedule_follow_up(lead, today)
        _logger.info("Created %s Service Leads for %s", len(created_leads), str(today))