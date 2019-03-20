# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, tools, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp


class PricelistComponent(models.TransientModel):
    _name = 'enquiry.pricelist.component'

    type_id = fields.Many2one('dms.price.component', string='Component Type')
    item_id = fields.Many2one('dms.enquiry2sale.order', string='Enquiry')
    price = fields.Float(
        'Price', digits=dp.get_precision('Product Price'))
    mandatory = fields.Boolean('Mandatory', default=False)


class Lead2OpportunityPartner(models.TransientModel):
    _name = 'dms.enquiry2sale.order'
    _description = 'Create Quote for Opportunity'
    _inherit = 'crm.partner.binding'

    @api.model
    def default_get(self, fields):
        """ Default get for name, opportunity_ids.
            If there is an exisitng partner link to the lead, find all existing
            opportunities links with this partner to merge all information together
        """
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        if self._context.get('active_id'):
            lead = self.env['crm.lead'].browse(self._context['active_id'])
            enquiry = lead.enquiry_id
            print(fields)
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
            if enquiry.partner_name:
                result['partner_name'] = enquiry.partner_name
            if enquiry.partner_mobile:
                result['partner_mobile'] = enquiry.partner_mobile
            if enquiry.partner_email:
                result['partner_email'] = enquiry.partner_email
        return result

    name = fields.Selection([
        ('convert', 'Convert to opportunity'),
        ('merge', 'Merge with existing opportunities')
    ], 'Conversion Action', required=True)

    action = fields.Selection([
        ('exist', 'Link to an existing customer'),
        ('create', 'Create a new customer')
    ], 'Related Customer', required=True)
    user_id = fields.Many2one('res.users', 'User')
    team_id = fields.Many2one('crm.team', 'Team')
    partner_id = fields.Many2one('res.partner', 'Customer')
    partner_name = fields.Char('Customer Name')
    partner_mobile = fields.Char('Customer Mobile')
    partner_email = fields.Char('Customer Email')
    product_id = fields.Many2one('product.template', string='Product', required=True, ondelete="cascade")
    product_color = fields.Many2one('product.attribute.value', string='Color')
    product_variant = fields.Many2one('product.attribute.value', string='Variant')
    pricelist = fields.Many2one('product.pricelist', string='Pricelist', ondelete="cascade")
    pricelist_components = fields.One2many('enquiry.pricelist.component', 'item_id',
                                           string='Price Components', ondelete="cascade")
    show_color = fields.Boolean('Color Visible', default=False)
    variant_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                               compute='compute_variant_attribute_values')
    color_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                             compute='compute_color_attribute_values')

    @api.onchange('product_id')
    def compute_variant_attribute_values(self):
        self.variant_attribute_values = None
        self.color_attribute_values = None
        self.product_color = None
        self.product_variant = None
        products = self.sudo().env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)])
        self.variant_attribute_values = products.mapped('attribute_value_ids').filtered(
            lambda attrib: attrib.attribute_id.name.lower() == 'variant')
        print(self.variant_attribute_values)

    @api.onchange('product_variant')
    def compute_color_attribute_values(self):
        products = self.sudo().env['product.product'].search(
            [('product_tmpl_id', '=', self.product_id.id), ('variant_value', '=', self.product_variant.name)])
        self.color_attribute_values = products.mapped('attribute_value_ids')
        self.show_color = True
        print(self.color_attribute_values)

    @api.multi
    def action_apply(self):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """

        if not self.partner_id:
            self.partner_id = self._find_matching_partner()
        customer = self.partner_id if self.partner_id else self._create_lead_partner()
        sale = self.env['sale.order']
        product = self.env['product.product'].search([('product_tmpl_id', '=', self.product_id.id),
                                                      ('color_value', '=', self.product_color.name),
                                                      ('variant_value', '=', self.product_variant.name)], limit=1)
        print("************************************************************************")
        for x in self.pricelist_components:
            print(x.type_id)
        if not product:
            raise UserError(_("Unable to create Quote as product not found"))
        values = {
            'team_id': self.team_id.id,
            'partner_id': customer.id,
            'user_id': self.user_id.id,
            'opportunity_id': self._context['active_id'],
            'pricelist_id': self.pricelist.id
        }
        order = sale.create(values)
        self._create_product_order_line(product, order)
        self._create_component_order_line(product, self.pricelist, order)
        if self.pricelist_components:
            self._create_additional_order_line(self.pricelist_components, order)

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
                for compos in item.component:
                    if compos.mandatory:
                        print("#####################", compos)
                        product = self.env['product.product'].search([('name', '=', compos.type_id.name)])
                        if not product:
                            product = self.env['product.product'].create(
                                self._prepare_component_product(compos.type_id.name))
                        vals = {
                            'product_id': product.id,
                            'name': compos.type_id.name,
                            'price_unit': compos.price,
                            'order_id': order.id
                        }
                        print(vals)
                        order_line = self.env['sale.order.line']
                        order_line.create(vals)

    def _create_additional_order_line(self, pricelist_components, order):
        print(pricelist_components)
        for item in pricelist_components:
            product = self.env['product.product'].search([('name', '=', item.type_id.name)])
            if not product:
                product = self.env['product.product'].create(self._prepare_component_product(item.type_id.name))
            vals = {
                'product_id': product.id,
                'name': item.type_id.name,
                'price_unit': item.price,
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

    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        email_split = tools.email_split(self.partner_email)

        return {
            'name': name,
            'mobile': self.partner_mobile,
            'email': email_split[0] if email_split else False,
            'customer': True
        }

    @api.model
    def _find_matching_partner(self):
        """ Try to find a matching partner regarding the active model data, like
            the customer's name, email, phone number, etc.
            :return int partner_id if any, False otherwise
        """

        # find the best matching partner for the active model
        Partner = self.env['res.partner']
        if self.partner_id:  # a partner is set already
            return self.partner_id

        if self.partner_name and self.partner_mobile:  # search through the existing partners based on the lead's partner and mobile
            partner = Partner.search([('name', 'ilike', '%' + lead.partner_name + '%'),
                                      ('mobile', 'ilike', '%' + self.partner_mobile + '%')], limit=1)
            return partner

        return False

    @api.multi
    def _create_lead_partner(self):
        """ Create a partner from lead data
            :returns res.partner record
        """
        partner = self.env['res.partner']
        if self.partner_name:
            return partner.create(self._create_lead_partner_data(self.partner_name, False))
