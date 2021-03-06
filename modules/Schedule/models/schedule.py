import logging
from odoo import api, fields, tools, models, _

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class Schedule(models.Model):
    _name = 'vehicle.schedule'

    name = fields.Char(
        'Schedule', required=True, help="Service Schedule")
    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id',
                              index=True, track_visibility='onchange',
                              help='When sending mails, the default email address is taken from the Sales Team.')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('service.schedule'))
    team_type = fields.Selection(
        [('sales', 'Sales'), ('insurance', 'Insurance'), ('finance', 'Finance'), ('service', 'Service'),
         ('business-center-insurance-rollover', 'Insurance Rollover'),
         ('business-center-insurance-renewal', 'Insurance Renewal'),
         ('business-center', 'Business-Center'), ('website', 'Website')], string='Team Type', default='sales',
        required=True,
        help="The type of this channel, it will define the resources this channel uses.")
    schedule_type = fields.Selection([
        ('period', 'Fixed Frequency'),
        ('normal', 'Time Frame'),
    ], string='Schedule Type', store=True, default='normal')
    allocation_type = fields.Selection([
        ('user', 'Specific User'),
        ('Lead', 'allocate to team Leads'),
        ('Round-Robin', 'Distribute to all users'),
    ], string='Allocation Type', store=True, default='Round-Robin')

    product_temp_id = fields.Many2one('product.template')
    product_id = fields.Many2one('product.product')
    product_category_id = fields.Many2one('product.category')
    parent_id = fields.Many2one('vehicle.schedule')
    days = fields.Integer('Frequency')
    delta = fields.Integer('Days for followup')
    active = fields.Boolean('active', default=True)
    product_radio = fields.Selection([
        ('Template', 'Product Template'),
        ('Product', 'Individual Product'),
        ('Category', 'Product Category'),
    ], string='Apply on', store=True, default='Product')
    product_type = fields.Selection([
        ('na', 'Not Applicable'),
        ('petrol', 'petrol'),
        ('diesel', 'diesel'),
        ('lpg', 'lpg'),
    ], string='Vehicle Type', store=True, default='na')
    opportunity_type = fields.Many2one('dms.opportunity.type')
    offset_days = fields.Integer('Offset Days')
    particular_day = fields.Datetime('Specific Day',default=False)

    @api.model
    def default_get(self, fields):
        rec = super(Schedule, self).default_get(fields)
        opportunity_type = self.env.context.get('default_opportunity_type')
        if opportunity_type:
            opportunity = self.env['dms.opportunity.type'].search([('name', '=', opportunity_type)], limit=1)
            rec['opportunity_type'] = opportunity.id
        return rec

    @api.model
    def prepare_leads(self, vehicle, date_follow_up, delta):
        return {
            'name': vehicle.partner_name + '-' + vehicle.product_id.name,
            'partner_name': vehicle.partner_name,
            'mobile': vehicle.partner_mobile,
            'street': vehicle.partner_id.street,
            'opportunity_type': self.opportunity_type.id,
            'date_deadline': date_follow_up + timedelta(delta),
            'vehicle_id': vehicle.id,
            'type': 'lead',
            'vin_no': vehicle.chassis_no,
            'registration_no': vehicle.registration_no,
            'dos': vehicle.date_order,
            'source': vehicle.source,
            'company_id': self.company_id.id
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
            date_deadline=today + timedelta(self.delta))

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

    @api.multi
    def generate_leads(self):
        for schedule in self:
            schedule._generate_leads()

    @api.model
    def allocate_users_for_schedule(self, leads):
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
        return leads

    @api.model
    def calculate_products_for_schedule(self, additional_filters):
        product_product = self.sudo().env['product.product']
        if self.product_category_id:
            product_template = self.sudo().env['product.template'].with_context(active_test=False).search(
                [('categ_id', '=', self.product_category_id.id)])
            if self.product_type == 'na':
                prods = product_product.with_context(active_test=False).search(
                    [('id', 'in', product_template.mapped('product_variant_ids').ids)])
            else:
                prods = product_product.with_context(active_test=False).search(
                    [('id', 'in', product_template.mapped('product_variant_ids').ids), ('fuel_type', '=', self.product_type)])
        elif self.product_temp_id:
            products = self.sudo().env['product.template'].with_context(active_test=False).search(
                [('id', '=', self.product_temp_id.id)])
            if self.product_type == 'na':
                prods = product_product.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids)])
            else:
                prods = product_product.with_context(active_test=False).search(
                    [('id', 'in', products.mapped('product_variant_ids').ids),
                     ('fuel_type', '=', self.product_type)])
        else:
            prods = self.product_id
        return prods

    @api.model
    def _get_vehicles_for_schedule(self, product_filters, vehicle_filters):
        prods = self.calculate_products_for_schedule(product_filters)
        filters = [('product_id', 'in', prods.ids), ('state', '=', 'sold'),('company_id','=',self.company_id.id),
                   ('date_order', '!=', False)]

        if vehicle_filters:
            filters += vehicle_filters
        vehicles = self.sudo().env['vehicle'].search(filters)
        print("%%%%% the vehicles", len(vehicles))
        return vehicles

    @api.model
    def check_duplicate(self, lead):
        dup = self.sudo().env['dms.vehicle.lead'].search([('name', '=', lead['name']),
                                                          ('partner_name', '=', lead['partner_name']),
                                                          ('mobile', '=', lead['mobile']),
                                                          ('date_deadline', '=',
                                                           lead['date_deadline'])])
        if dup:
            return True

    @api.model
    def _generate_leads(self):
        # Need child class to implement this.
        pass
