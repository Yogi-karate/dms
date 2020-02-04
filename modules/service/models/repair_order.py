# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Service Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    vehicle_id = fields.Many2one('vehicle')
    location_id = fields.Many2one('stock.location', string='Preferred location of service', track_visibility='onchange')
    remarks = fields.Char('Remarks')
    dop = fields.Datetime('Date and Time of Pick-Up', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('service.booking'))
    booking_type = fields.Selection([
        ('pickup', 'Pick-Up'),
        ('walk', 'Walk-In'),
    ], string='Booking Type', store=True, default='pickup', track_visibility='onchange')

    pick_up_address = fields.Char('Pick-up Address')
    due_date = fields.Datetime(string='Service Due Date')
    partner_name = fields.Char('Customer name',required=True)
    mobile = fields.Char('Customer number',required=True)
    mail = fields.Char('Customer Mail ID')
    vehicle_model = fields.Many2one('product.template')
    product_color = fields.Many2one('product.attribute.value', string='Color')
    product_variant = fields.Many2one('product.attribute.value', string='Variant')
    variant_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                               compute='compute_variant_attribute_values')
    color_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                             compute='compute_color_attribute_values')
    user_id = fields.Many2one('res.users', string='Salesperson',
                              default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True)
    service_type = fields.Many2one('service.type')
    active = fields.Boolean(default=True)
    reg_no = fields.Char('Registration Number')
    status = fields.Selection([
        ('new', 'Pending'),
        ('won', 'Reported'),
        ('lost', 'Not Reported'),
    ], string='Status', store=True, default='new', track_visibility='onchange')

    @api.onchange('vehicle_model')
    def compute_variant_attribute_values(self):
        if self.variant_attribute_values or self.color_attribute_values:
            self.product_color = None
            self.product_variant = None
        self.variant_attribute_values = None
        self.color_attribute_values = None
        products = self.sudo().env['product.product'].search([('product_tmpl_id', '=', self.vehicle_model.id)])
        self.variant_attribute_values = products.mapped('attribute_value_ids')

        print(self.variant_attribute_values)

    @api.onchange('product_variant')
    def compute_color_attribute_values(self):
        products = self.sudo().env['product.product'].search(
            [('product_tmpl_id', '=', self.vehicle_model.id), ('variant_value', '=', self.product_variant.name)])
        self.color_attribute_values = products.mapped('attribute_value_ids')
        print(self.color_attribute_values)




class RepairOrder(models.Model):
    _name = 'repair.order'
    _inherit = ['sale.order']
    assessment_id = fields.Many2one('assessment.sheet')
    name  = fields.Char('name')
    order_line = fields.One2many('repair.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    partner_mobile = fields.Char('Mobile', required=True)
    @api.onchange('assessment_id')
    def _get_partner(self):
        self.partner_id = self.assessment_id.vehicle_id.partner_id.id
        self.partner_mobile = self.assessment_id.partner_mobile
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('repair.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('repair.order') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id',
                                                   partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(RepairOrder, self).create(vals)
        return result

class SaleOrderLine(models.Model):
    _name = 'repair.order.line'
    _description = 'Repair Order Line'
    _inherit = ['sale.order.line']
    order_id = fields.Many2one('repair.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    product_id = fields.Many2one('product.product', string='Product', domain=['|',('product_tmpl_id.categ_id.name', '=', 'Services'),('product_tmpl_id.categ_id.name', '=', 'Spare Parts')],
                                 change_default=True, ondelete='restrict')
