# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from odoo.osv import expression

_logger = logging.getLogger(__name__)

from werkzeug.urls import url_encode

class AccountInvoiceLine(models.Model):
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"
    _description = "Invoice Line"
    _order = "invoice_id,sequence,id"

    discount_price = fields.Float('Discount', digits=dp.get_precision('Product Price'), default=0.0)

    @api.one
    @api.depends('price_unit', 'discount','discount_price', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
        'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        if self.discount_price:
            price = self.price_unit - self.discount_price
        else:
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            currency = self.invoice_id.currency_id
            date = self.invoice_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.invoice_id.company_id.currency_id, self.company_id or self.env.user.company_id, date or fields.Date.today())
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign
        

class DmsSaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'

    user_name = fields.Char(compute='_compute_consultant')
    user_mobile = fields.Char(compute='_compute_consultant')
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
        ('cash', 'Cash'),
    ], string='Finance Type', store=True, default='in')
    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    finance_pmt = fields.Float('Finance Amount')
    finance_payment_date = fields.Date('Finance Payment Date')
    margin_pmt = fields.Float('Margin Money Amount')
    margin_payment_date = fields.Date('Margin Money Payment Date')
    delivery_date = fields.Date('Delivery Date')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('booked', 'Booked'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'On-Hold'),
        ('2', 'Medium'),
        ('3', 'High'),
    ])
    stock_status = fields.Selection([
        ('delivered', 'Delivered'),
        ('allotted', 'Allotted'),
        ('purchase-pending', 'Yet-To-Order'),
        ('purchase-confirmed', 'Purchase Order Confirmed'),
        ('purchase-draft', 'Purchase Order Placed'),
    ], string='Allocation Status', compute='_calculate_allocation', default='purchase-pending', store=True)
    dob = fields.Datetime('Date of Booking')
    product_name = fields.Char('Model', compute='_calculate_product')
    product_variant = fields.Char('Variant', compute='_calculate_product')
    product_color = fields.Char('Color', compute='_calculate_product')
    balance_amount = fields.Float('Balance Amount', compute='_calculate_residual_amount')
    booking_amt = fields.Float(' Booking Amount')
    product_id = fields.Many2one('product.product', string='product', compute='_calculate_product')

    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel','booked'}

    @api.multi
    def _calculate_product(self):
        for order in self:
            if order.order_line:
                order.product_id = order.order_line[0].product_id

    @api.multi
    def action_cancel(self):
        if self.state == 'booked' and self.balance_amount > 0:
            raise UserError(
                _('You cannot cancel a booking with payments pending'))
        return self.write({'state': 'cancel'})

    @api.depends('name')
    def _compute_consultant(self):
        """ Compute difference between create date and open date """
        user = self.env['res.users'].sudo().search([('id', '=', self.user_id.id)])
        self.user_name = user.partner_id.name
        if user.partner_id.mobile:
            self.user_mobile = user.partner_id.mobile
        else:
            self.user_mobile = user.partner_id.phone

    @api.multi
    def _calculate_residual_amount(self):
        for order in self:
            balance = 0
            for invoice in order.invoice_ids:
                balance += invoice.residual
            order.balance_amount = balance

    def _calculate_product(self):
        for order in self:
            if len(order.order_line) < 1:
                continue
            first_order_line = order.order_line[0]
            if first_order_line:
                print(" the product id for order is ", first_order_line.product_id, order)
                order.product_name = first_order_line.product_id.name
                order.product_variant = first_order_line.product_id.variant_value
                order.product_color = first_order_line.product_id.color_value

    @api.depends('dob', 'delivery_date')
    def _calculate_allocation(self):
        for order in self:
            if order.state == 'booked':
                vehicle = self.sudo().env['vehicle'].search([('order_id', '=', order.id)])
                if vehicle:
                    order.stock_status = 'allotted'
                else:
                    order.stock_status = 'purchase-pending'
                for pick in order.picking_ids:
                    if pick.state == 'done':
                        order.stock_status = 'delivered'
            else:
                order.state = False

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        team_id = self.env.user.sale_team_id
        if team_id:
            warehouse_ids = [team_id.location_id.get_warehouse()]
        else:
            warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids[0]

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id)

    def write(self, values):
        self.ensure_one()
        location_name = self.warehouse_id.name.lower()
        if location_name and 'state' in values and values['state'] == 'booked':
            if 'tirumalgiri' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.tir') or _('New')
            if 'mettuguda' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.met') or _('New')
            if 'ranigunj' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.nac') or _('New')
            if 'nacharam' in location_name:
                values['name'] = self.env['ir.sequence'].next_by_code('sale.order.nac') or _('New')
        return super(DmsSaleOrder, self).write(values)

    @api.depends('state', 'order_line.invoice_status', 'order_line.invoice_lines')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        # Ignore the status of the deposit product
        deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
        line_invoice_status_all = [(d['order_id'][0], d['invoice_status']) for d in
                                   self.env['sale.order.line'].read_group(
                                       [('order_id', 'in', self.ids), ('product_id', '!=', deposit_product_id.id)],
                                       ['order_id', 'invoice_status'], ['order_id', 'invoice_status'], lazy=False)]
        for order in self:
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(
                lambda r: r.type in ['out_invoice', 'out_refund'])
            # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
            # 'account.invoice.refund')
            # use like as origin may contains multiple references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([('origin', 'like', order.name), ('company_id', '=', order.company_id.id),
                                          ('type', 'in', ('out_invoice', 'out_refund'))])
            invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])

            # Search for refunds as well
            domain_inv = expression.OR([
                ['&', ('origin', '=', inv.number), ('journal_id', '=', inv.journal_id.id)]
                for inv in invoice_ids if inv.number
            ])
            if domain_inv:
                refund_ids = self.env['account.invoice'].search(expression.AND([
                    ['&', ('type', '=', 'out_refund'), ('origin', '!=', False)],
                    domain_inv
                ]))
            else:
                refund_ids = self.env['account.invoice'].browse()

            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            print(line_invoice_status)
            if order.state == 'cancel' and len(line_invoice_status) > 0 and line_invoice_status[0] == 'invoiced':
                invoice_status = 'invoiced'
            elif order.state not in ('sale', 'done','booked'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                invoice_status = 'invoiced'
            elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                invoice_status = 'upselling'
            else:
                invoice_status = 'no'
            order.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.multi
    def unlink(self):
        for order in self:
            if order.invoice_status == 'invoiced':
                raise UserError(
                    _('You cannot delete an invoiced booking, even if you cancel.'))
            elif order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can not delete a sent quotation or a confirmed sales order. You must first cancel it.'))
        return super(DmsSaleOrder, self).unlink()


class DmsSaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = 'sale.order.line'

    discount_price = fields.Float('Discount', digits=dp.get_precision('Product Price'), default=0.0)

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state == 'cancel' and line.qty_invoiced == 1:
                line.invoice_status = 'invoiced'
            elif line.state not in ('sale', 'done' ,'booked'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.multi
    def unlink(self):
        if self.filtered(lambda line: line.state in ('sale','booked', 'done') and (line.invoice_lines or not line.is_downpayment)):
            raise UserError(_(
                'You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        return super(DmsSaleOrderLine, self).unlink()
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

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            # if line.is_downpayment and line.qty_invoiced == 0.0:
            #     line.qty_invoiced = 1
            if line.order_id.state in ['sale', 'booked', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id

        if not account and self.product_id:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos and account:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'discount_price': self.discount_price,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'display_type': self.display_type,
        }
        return res
    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
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
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
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
        return [inv for inv in invoices.values()]

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

    @api.model
    def discount_update(self):
        orders = self.env['sale.order'].search([('state', '=', 'booked')])
        for order in orders:
            for line in order.order_line:
                if line.discount_price:
                    for invoice_line in line.invoice_lines:
                        print("the invoice line is ", invoice_line)
                        if invoice_line.price_unit == line.price_unit:
                            invoice_line.write({'discount_price': line.discount_price})

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

    @api.model
    def order_discount_update(self):
        _logger.info("---------Order discount update process started ---------")
        self.discount_update()
        _logger.info("---------Order discount update process completed ---------")


class DmsBookingAllocation(models.Model):
    _name = "booking.order.allocation"

    def process_allocations(self):
        _logger.info("---------Order allocation process started ---------")
        self._process_allocations()
        _logger.info("---------Order allocation process completed ---------")

    def _update_state(self, orders, state):
        for order in orders:
            print("order and state to be changed ", order, state)
            order.write({'stock_status': state})

    def _calculate_purchase_state(self, products_to_be_allocated):

        for prod in products_to_be_allocated.keys():
            print("the product we are working on is ", prod)
            order_list = products_to_be_allocated[prod]
            moves = self.env['stock.move'].search(
                [('state', 'not in', ['done', 'cancel']), ('product_id', '=', prod.id),
                 ('picking_id.picking_type_code', '=', 'incoming')])
            if moves:
                print("the orders to be confirmed", order_list[:len(moves)])
                self._update_state(order_list[:len(moves)], 'purchase-confirmed')
            if len(moves) < len(order_list):
                purchases_lines = self.env['purchase.order.line'].search(
                    [('order_id.state', '=', 'draft'), ('product_id', '=', prod.id)])
                if purchases_lines:
                    draft_counter = len(moves) + len(purchases_lines)
                    print("the orders to be draft", order_list[len(moves):draft_counter])
                    self._update_state(order_list[len(moves):draft_counter], 'purchase-draft')
                    if draft_counter < len(order_list):
                        self._update_state(order_list[draft_counter:], 'purchase-pending')
                else:
                    print("the orders to be yet to order", order_list[len(moves):])
                    self._update_state(order_list[len(moves):], 'purchase-pending')

    def _process_allocations(self):
        orders = self.env['sale.order'].search([('state', '=', 'booked')])
        products_to_be_allocated = {}
        for order in orders:
            vehicle = self.sudo().env['vehicle'].search([('order_id', '=', order.id)])
            if vehicle:
                order.stock_status = 'allotted'
                continue
            else:
                if order.picking_ids and order.picking_ids.state == 'done':
                    order.stock_status = 'delivered'
                    continue
                else:
                    product_id = order.order_line[0].product_id
                    prod_orders = products_to_be_allocated.get(product_id, False)
                    print("the prod orders ", prod_orders)
                    if prod_orders:
                        prod_orders.append(order)
                    else:
                        products_to_be_allocated.update({order.order_line[0].product_id: [order]})
        print("The products to be allocated are ", products_to_be_allocated)
        self._calculate_purchase_state(products_to_be_allocated)


