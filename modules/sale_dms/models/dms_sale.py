# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)

from werkzeug.urls import url_encode


class DmsSaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
    ], string='Finance Type', store=True, default='in')
    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    payment_date = fields.Datetime('Payment Date')
    delivery_date = fields.Datetime('Delivery Date')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('booked', 'Booked'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'On-Hold'),
        ('2', 'Medium'),
        ('3', 'High'),
    ])
    stock_status = fields.Selection([
        ('allotted', 'Allotted'),
        ('not-allotted', 'Not-Allotted'),
        ], string='Status', compute='_calculate_product', default='not-allotted')
    dob = fields.Datetime('Date of Booking')
    product_name = fields.Char('Model',compute='_calculate_product')
    product_variant = fields.Char('Variant',compute='_calculate_product')
    product_color = fields.Char('Color',compute='_calculate_product')
    balance_amount = fields.Float('Balance Amount',compute='_calculate_residual_amount')


    def _calculate_residual_amount(self):
        for order in self:
            balance = 0
            for invoice in order.invoice_ids:
                balance += invoice.residual
            order.balance_amount = balance

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            print(line.qty_invoiced, ">>>>>>>>>>>>>>>>>>>>>>>>>>>>", line.product_uom_qty)
            if line.order_id.state in ['sale','booked' ,'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    def _calculate_product(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'draft' or pick.state == 'confirmed' or pick.state == 'waiting':
                    order.stock_status = 'not-allotted'
                else:
                    order.stock_status = 'allotted'
            count = 0
            order.blnc_amt = order.amount_total
            for x in order.order_line:
                if count == 0:
                    order.product_name = x.product_id.name
                    order.product_variant = x.product_id.variant_value
                    order.product_color = x.product_id.color_value
                count += 1
                print(x.product_id)
                if x.is_downpayment:
                    order.blnc_amt = order.amount_total - x.price_unit
            print("000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
            print(x.price_unit, "---------", order.name, "..............",order.amount_total,"..............",order.blnc_amt)
    @api.multi
    def _force_lines_to_invoice_policy_order(self):
        for line in self.order_line:
            if self.state in ['sale','booked', 'done']:
                print(line.qty_invoiced,">>>>>>>>>>>>>>>>>>>>>>>>>>>>",line.product_uom_qty)
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0


    @api.multi
    def _write(self, values):
        """ Override of private write method in order to generate activities
        based in the invoice status. As the invoice status is a computed field
        triggered notably when its lines and linked invoice status changes the
        flow does not necessarily goes through write if the action was not done
        on the SO itself. We hence override the _write to catch the computation
        of invoice_status field. """
        print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        print(values)
        print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",self.team_id.location_id.name)
        location_name = self.team_id.location_id.name
        if not location_name:
            print("no location")
        else:
            if 'state' in values and values['state'] == 'booked':
                    if 'Tirumalgiri' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.tir') or _('New')
                    if 'Mettuguda' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.met') or _('New')
                    if 'Ranigunj' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.rani') or _('New')
                    if 'Nacharam' in location_name:
                        values['name'] = self.env['ir.sequence'].next_by_code('sale.order.nac') or _('New')

        # if values.get('name', _('New')) == _('New'):
        #     if 'company_id' in vals:
        #         values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code('sale.order') or _('New')
        #     else:
        #         values['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
        if self.env.context.get('mail_activity_automation_skip'):
            return super(DmsSaleOrder, self)._write(values)

        if 'invoice_status' in values:
            if values['invoice_status'] == 'upselling':
                filtered_self = self.search([('id', 'in', self.ids),
                                             ('user_id', '!=', False),
                                             ('invoice_status', '!=', 'upselling')])
                filtered_self.activity_unlink(['sale.mail_act_sale_upsell'])
                for order in filtered_self:
                    order.activity_schedule(
                        'sale.mail_act_sale_upsell',
                        user_id=order.user_id.id,
                        note=_(
                            "Upsell <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer <a href='#' data-oe-model='%s' data-oe-id='%s'>%s</a>") % (
                                 order._name, order.id, order.name,
                                 order.partner_id._name, order.partner_id.id, order.partner_id.display_name))

        return super(DmsSaleOrder, self)._write(values)

    @api.multi
    def action_invoice_create(self,so_line, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)

            # We only want to create sections that have at least one invoiceable line
            pending_section = None

            for line in order.order_line:

                if line.order_id.state in ['sale', 'booked', 'done']:
                    print(line.qty_to_invoice,
                          "------------------------------------------------------------------------------------------if case")
                    if line.product_id.invoice_policy == 'order':
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
                    if line.is_downpayment:
                        line.qty_to_invoice = -1

                else:
                    print(line.qty_to_invoice,"------------------------------------------------------------------------------------------else case")
                    line.qty_to_invoice = 0


                print(line.is_downpayment,"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",line.name)
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    print(group_key, "-------------------------------------------group key","-----------",line.name)
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)
                # if line.is_downpayment:
                #     print(line.name,"")
                #     if pending_section:
                #         pending_section.invoice_line_create(invoices[group_key].id, -1)
                #         pending_section = None
                #     line.invoice_line_create(invoices[group_key].id, -1)
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    print(line.name,"-----------------oooooooo----",line.qty_to_invoice)
                    if pending_section:
                        pending_section.invoice_line_create(invoices[group_key].id, pending_section.qty_to_invoice)
                        pending_section = None
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})
            sale_orders = references[invoices[group_key]]
            if len(sale_orders) == 1:
                invoices[group_key].reference = sale_orders.reference

        if not invoices:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        for invoice in invoices.values():
            print(invoice, "-----")
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                print(line.name, "-----",line.quantity)
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            # Idem for partner
            so_payment_term_id = invoice.payment_term_id.id
            invoice._onchange_partner_id()
            # To keep the payment terms set on the SO
            invoice.payment_term_id = so_payment_term_id
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

class DmsSaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = 'sale.order.line'

    discount_price = fields.Float('Discount', digits=dp.get_precision('Product Price'), default=0.0)

    @api.depends('product_uom_qty', 'discount_price', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit - (line.discount_price or 0.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id,
                                            partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('price_unit', 'discount_price')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit - line.discount_price


class SaleCleanup(models.TransientModel):
    _name = 'dms.order.cleanup'
    name = fields.Char('Customer Name')
    mobile = fields.Char('Customer Mobile')
    order_no = fields.Char('Order No')
    state = fields.Selection([
        ('draft', 'New'),
        ('duplicate', 'Duplicate'),
        ('cancel', 'Cancelled'),
        ('no_order', 'No Order'),
        ('complete', 'Complete'),
    ], string='Status', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    @api.multi
    def reassign_partner(self):
        _logger.info("The number of records to process =>" + str(len(self)))
        for customer in self:
            order = self.env['sale.order'].search([('name', '=', customer.order_no)], limit=1)
            partner = self.env['res.partner'].search(
                [('name', 'ilike', customer.name), ('mobile', '=', customer.mobile)])
            if partner and len(partner) > 1:
                _logger.info("Duplicate customer in System : %s", customer)
                customer.write({'state': 'duplicate'})
                continue
            if not order:
                _logger.info("No such Order to reassign : %s", customer)
                customer.write({'state': 'no_order'})
                continue
            if not partner:
                _logger.info("No such customer to reassign : %s", customer)
                customer.write({'state': 'cancel'})
                continue
            order.write({'partner_id': partner.id})
            vehicle = self.env['vehicle'].search([('order_id', '=', order.id)])
            if not vehicle:
                _logger.info("No such vehicle : %s", order)
                continue
            vehicle.write({'partner_id': partner.id})
            vehicle_leads = self.env['dms.vehicle.lead'].search([('vehicle_id', '=', vehicle.id)])
            for lead in vehicle_leads:
                lead.write({
                    'name': vehicle.partner_name + '-' + vehicle.product_id.name,
                    'partner_name': vehicle.partner_name,
                    'mobile': vehicle.partner_mobile
                })
            customer.write({'state': 'complete'})

    @api.model
    def order_clean_up(self):
        _logger.info("---------Order cleanup process started ---------")
        self.env['dms.order.cleanup'].search([('state', '=', 'draft')]).reassign_partner()
        _logger.info("---------Order cleanup process completed ---------")
