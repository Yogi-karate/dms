# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Service Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    vehicle_id = fields.Many2one('vehicle')



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
