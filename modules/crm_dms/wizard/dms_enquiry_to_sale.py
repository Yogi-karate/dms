# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class Lead2OpportunityPartner(models.TransientModel):
    _name = 'dms.enquiry2sale.order'
    _description = 'Create Quote for Opportunity (not in mass)'

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        if self._context.get('active_id'):
            tomerge = {int(self._context['active_id'])}

            partner_id = result.get('partner_id')
            lead = self.env['crm.lead'].browse(self._context['active_id'])
            enquiry = lead.enquiry_id
            email = lead.partner_id.email if lead.partner_id else lead.email_from
            tomerge.update(self._get_duplicated_leads(partner_id, email, include_lost=True).ids)

            if 'action' in fields and not result.get('action'):
                result['action'] = 'exist' if partner_id else 'create'
            if 'partner_id' in fields:
                result['partner_id'] = lead.partner_id.id
            if 'name' in fields:
                result['name'] = 'merge' if len(tomerge) >= 2 else 'convert'
            if lead.user_id:
                result['user_id'] = lead.user_id.id
            if lead.team_id:
                result['team_id'] = lead.team_id.id
            if enquiry.product_color:
                result['product_color'] = enquiry.product_color.id
            if enquiry.product_variant:
                result['product_variant'] = enquiry.product_variant.id
            if enquiry.product_id:
                result['product_id'] = enquiry.product_id.id
            if not partner_id and not lead.contact_name:
                result['action'] = 'nothing'
        return result

    name = fields.Selection([
        ('convert', 'Convert to opportunity'),
        ('merge', 'Merge with existing opportunities')
    ], 'Conversion Action', required=True)

    action = fields.Selection([
        ('exist', 'Link to an existing customer'),
        ('create', 'Create a new customer'),
        ('nothing', 'Do not link to a customer')
    ], 'Related Customer', required=True)
    user_id = fields.Many2one('res.users', 'User')
    team_id = fields.Many2one('crm.team', 'Team')
    partner_id = fields.Many2one('res.partner', 'Customer')
    product_id = fields.Many2one('product.template', string='Product', required=True)
    product_color = fields.Many2one('product.template.attribute.value', string='Color')
    product_variant = fields.Many2one('product.template.attribute.value', string='Variant')
    pricelist = fields.Many2one('product.pricelist', string='Pricelist')

    @api.onchange('action')
    def onchange_action(self):
        if self.action == 'exist':
            self.partner_id = self._find_matching_partner()
        else:
            self.partner_id = False

    @api.onchange('user_id')
    def _onchange_user(self):
        """ When changing the user, also set a team_id or restrict team id
            to the ones user_id is member of.
        """
        if self.user_id:
            if self.team_id:
                user_in_team = self.env['crm.team'].search_count(
                    [('id', '=', self.team_id.id), '|', ('user_id', '=', self.user_id.id),
                     ('member_ids', '=', self.user_id.id)])
            else:
                user_in_team = False
            if not user_in_team:
                values = self.env['crm.lead']._onchange_user_values(self.user_id.id if self.user_id else False)
                self.team_id = values.get('team_id', False)

    @api.model
    def _get_duplicated_leads(self, partner_id, email, include_lost=False):
        """ Search for opportunities that have the same partner and that arent done or cancelled """
        return self.env['crm.lead']._get_duplicated_leads_by_emails(partner_id, email, include_lost=include_lost)

    # NOTE JEM : is it the good place to test this ?
    @api.model
    def view_init(self, fields):
        """ Check some preconditions before the wizard executes. """
        for lead in self.env['crm.lead'].browse(self._context.get('active_ids', [])):
            if lead.probability == 100:
                raise UserError(_("Closed/Dead leads cannot be converted into opportunities."))
        return False

    @api.multi
    def _convert_opportunity(self, vals):
        self.ensure_one()

        res = False

        leads = self.env['crm.lead'].browse(vals.get('lead_ids'))
        for lead in leads:
            self_def_user = self.with_context(default_user_id=self.user_id.id)
            partner_id = \
                self_def_user._create_partner(
                    lead.id, self.action, vals.get('partner_id') or lead.partner_id.id)
            res = lead.convert_opportunity(partner_id, [], False)
        user_ids = vals.get('user_ids')

        leads_to_allocate = leads
        if self._context.get('no_force_assignation'):
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate.allocate_salesman(user_ids, team_id=(vals.get('team_id')))

        return res

    @api.multi
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        sale = self.env['sale.order']
        product = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id),
                                                      ('color_value', '=', self.product_color.name),
                                                      ('variant_value', '=', self.product_variant.name)], limit=1)
        print("************************************************************************")
        print(product)
        if not product:
            raise UserError(_("Unable to create Quote as product not found"))
        values = {
            'team_id': self.team_id.id,
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'opportunity_id': self._context['active_id'],
            'pricelist_id': self.pricelist.id
        }

        if self.partner_id:
            values['partner_id'] = self.partner_id.id
        order = sale.create(values)

        self._create_product_order_line(product, order)
      #  self._create_component_order_line(product, self.pricelist, order)


    def _create_product_order_line(self, product, order):
        order_line = self.env['sale.order.line']
        vals = {
            'product_id': product.id,
            'name': product.name,
            'order_id': order.id
        }
        order_line.create(vals)

    def _create_component_order_line(self, product, pricelist, order):
        items = pricelist.item_ids.search(
            ['|', ('product_id', '=', product.id), ('product_tmpl_id', '=', product.product_tmpl_id.id)])
        for item in items:
            if item.pricelist_id.id == self.pricelist.id:
                print("#####################", item)
                for compos in item.component:
                    product = self.env['product.product'].search([('name', '=', compos.type_id.name)])
                    if not product:
                        product = self.env['product.product'].create(self._prepare_component_product(compos.type_id.name))
                    vals = {
                        'product_id': product.id,
                        'name': compos.type_id.name,
                        'price_unit': compos.price,
                        'order_id': order.id
                    }
                    print(vals)
                    order_line = self.env['sale.order.line']
                    order_line.create(vals)

    def _prepare_component_product(self, component_name):
        return {
            'name': component_name,
            'type': 'service',
            'company_id': False,
            'taxes_id': []
        }

    def _create_partner(self, lead_id, action, partner_id):
        """ Create partner based on action.
            :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        # TODO this method in only called by Lead2OpportunityPartner
        # wizard and would probably diserve to be refactored or at least
        # moved to a better place
        if action == 'each_exist_or_create':
            partner_id = self.with_context(active_id=lead_id)._find_matching_partner()
            action = 'create'
        result = self.env['crm.lead'].browse(lead_id).handle_partner_assignation(action, partner_id)
        return result.get(lead_id)
