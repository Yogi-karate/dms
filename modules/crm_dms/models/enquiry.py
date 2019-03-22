from odoo import api, fields, models, tools, SUPERUSER_ID, _

from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
import re


class Enquiry(models.Model):
    _name = "dms.enquiry"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Enquiry', index=True)
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', track_sequence=1,
                                 index=True,
                                 help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.")
    active = fields.Boolean('Active', default=True, track_visibility=True)
    team_id = fields.Many2one('crm.team', string='Sales Team', oldname='section_id',
                              default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(
                                  user_id=self.env.uid),
                              index=True, track_visibility='onchange',
                              help='When sending mails, the default email address is taken from the Sales Team.')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('dms.enquiry'))
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='open')
    product_id = fields.Many2one('product.template', string='Product', required=True)
    product_color = fields.Many2one('product.attribute.value', string='Color')
    product_variant = fields.Many2one('product.attribute.value', string='Variant')
    opportunity_ids = fields.One2many('crm.lead', 'enquiry_id', string='Opportunities')
    type_ids = fields.Many2many('dms.opportunity.type', 'enquiry_opportunity_type_rel', 'enquiry_id',
                                'opportunity_type_id', string='Types', required=True,
                                track_visibility='onchange')
    categ_ids = fields.Many2many('product.category', 'enquiry_category_rel', 'enquiry_id',
                                 'id', string='Opportunity Categories', compute='_compute_categories',
                                 track_visibility='onchange')
    product_updatable = fields.Boolean(compute='_compute_product_updatable', string='Can provide product details',
                                       readonly=True)
    finance_updatable = fields.Boolean(compute='_compute_finance_updatable', string='Can provide finance details',
                                       readonly=True)
    insurance_updatable = fields.Boolean(compute='_compute_insurance_updatable', string='Can provide insurance details',
                                         readonly=True)
    opportunity_count = fields.Integer('# Meetings', compute='_compute_opportunity_count')
    date_follow_up = fields.Date('Follow-Up Date', help="Estimate of the date on which the opportunity will be won.",
                                 required=True)
    partner_name = fields.Char('Customer Name', required=True)
    partner_mobile = fields.Char('Customer Mobile', required=True)
    partner_email = fields.Char('Customer Email')
    description = fields.Text('Notes', track_visibility='onchange', track_sequence=6)

    # finance fields added by Yoganand on 31-01-2019
    financier_name = fields.Many2one('res.bank', string='Financier', help="Bank for finance")
    finance_amount = fields.Float('Amount', digits=dp.get_precision('Product Price'), default=0.0)
    finance_agreement_date = date_order = fields.Datetime(string='Finance Agreement Date', default=fields.Datetime.now)
    loan_tenure = fields.Char('Tenure', help="Loan Tenure")
    loan_amount = fields.Float('Loan Amount', digits=dp.get_precision('Product Price'), default=0.0)
    loan_approved_amount = fields.Float('Approved Amount', digits=dp.get_precision('Product Price'), default=0.0)
    loan_rate = fields.Float("Rate of Interest", digits=(2, 2), help='The rate of interest for loan')
    loan_emi = fields.Float('EMI', digits=dp.get_precision('Product Price'), default=0.0)
    loan_commission = fields.Float('Commission ', digits=dp.get_precision('Product Price'), default=0.0)
    finance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
    ], string='Finance Type', store=True, default='in')

    # insurance fields added by Yoganand on 31/01/2019
    insurance_company = fields.Char('Insurance Company', String="Insurance Company")
    policy_no = fields.Char('Policy No.')
    insurance_valid_from = fields.Datetime(string='Insurance Valid From')
    insurance_valid_to = fields.Datetime(string='Insurance Valid To')
    insurance_type = fields.Selection([
        ('in', 'in-house'),
        ('out', 'out-house'),
    ], string='Insurance Type', store=True, default='in')
    policy_punch_via = fields.Selection([
        ('covernote', 'Covernote'),
        ('hap', 'HAP'),
        ('nonhap', 'Non-HAP')
    ], string='Policy Punch Via', store=True, default='hap')
    currency_id = fields.Many2one(
        'res.currency', string='Currency')
    idv = fields.Monetary('IDV', currency_field='currency_id')
    premium_amount = fields.Monetary('Premium Amount', currency_field='currency_id')
    source_id = fields.Many2one('utm.source', string='Source', required=True)
    medium_id = fields.Many2one('utm.medium', string='Medium')
    show_color = fields.Boolean('Color Visible', default=False)
    variant_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                               compute='compute_variant_attribute_values')
    color_attribute_values = fields.One2many('product.attribute.value', string='attributes',
                                             compute='compute_color_attribute_values')

    @api.onchange('product_id')
    def compute_variant_attribute_values(self):
        if self.variant_attribute_values or self.color_attribute_values:
            self.product_color = None
            self.product_variant = None
        self.variant_attribute_values = None
        self.color_attribute_values = None
        products = self.sudo().env['product.product'].search([('product_tmpl_id', '=', self.product_id.id)])
        self.variant_attribute_values = products.mapped('attribute_value_ids')

        print(self.variant_attribute_values)

    @api.onchange('product_variant')
    def compute_color_attribute_values(self):
        products = self.sudo().env['product.product'].search(
            [('product_tmpl_id', '=', self.product_id.id), ('variant_value', '=', self.product_variant.name)])
        self.color_attribute_values = products.mapped('attribute_value_ids')
        self.show_color = True
        print(self.color_attribute_values)

    @api.depends('type_ids')
    @api.multi
    def _compute_product_updatable(self):
        is_vehicle = False
        for type_id in self.type_ids:
            if 'vehicle' in type_id.name.lower() or 'new' in type_id.name.lower():
                is_vehicle = True
        self.product_updatable = is_vehicle

    @api.depends('type_ids')
    @api.multi
    def _compute_finance_updatable(self):
        is_finance = False
        for type_id in self.type_ids:
            if 'finance' in type_id.name.lower():
                is_finance = True
        self.finance_updatable = is_finance

    @api.depends('type_ids')
    @api.multi
    def _compute_insurance_updatable(self):
        is_insurance = False
        for type_id in self.type_ids:
            if 'insurance' in type_id.name.lower():
                is_insurance = True
        self.insurance_updatable = is_insurance

    @api.constrains('partner_mobile')
    @api.multi
    def _valid_mobile(self):
        pattern = re.compile(r'^[0-9]{10}')
        for enquiry in self:
            if not pattern.match(enquiry.partner_mobile):
                raise ValidationError(_("Please Enter a Valid Mobile Number"))

    @api.multi
    def _compute_categories(self):
        ids = []
        for type_id in self.type_ids:
            ids.append(type_id.categ_id.id)
        self.categ_ids = ids

    @api.onchange('type_ids')
    def _on_change_type(self):
        print(self.type_ids)
        self._compute_categories()
        return

    @api.depends('type_ids')
    @api.multi
    def _compute_type_changes(self):
        print(self.type_ids)
        leads = self.env['crm.lead'].search([('enquiry_id', '=', self.id)])
        print(leads)
        if leads:
            raise UserError(_('Cannot Change Types after Sub Enquiry creation - Please Create a new enquiry'))

    @api.multi
    def _compute_opportunity_count(self):
        # meeting_data = self.env['calendar.event'].read_group([('enquiry_id', 'in', self.ids)], ['enquiry_id'],
        # ['enquiry_id'])
        # mapped_data = {m['enquiry_id'][0]: m['enquiry_id_count'] for m in meeting_data}
        for enquiry in self:
            enquiry.opportunity_count = len(enquiry.opportunity_ids)

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        print(vals)
        if 'name' not in vals:
            product_name = self.env['product.template'].browse(vals['product_id']).name
            vals['name'] = product_name
            if 'partner_name' in vals:
                vals['name'] += '-' + vals['partner_name']
        res = super(Enquiry, self).create(vals)
        res._create_opportunities()
        return res

    @api.model
    def _prepare_opportunities(self, type):
        # customer = self._create_lead_partner()
        return {
            'name': type.name + '-' + self.product_id.name,
            'partner_name': self.partner_name,
            'mobile': self.partner_mobile,
            'enquiry_id': self.id,
            'opportunity_type': type.id,
            'date_deadline': self.date_follow_up,
            'type': 'opportunity'
        }

    @api.model
    def _schedule_follow_up(self, lead):
        lead.activity_schedule(
            'crm_dms.mail_activity_data_follow_up',
            user_id=lead.user_id.id,
            note=_(
                "Follow up  on  <a href='#' data-oe-model='%s' data-oe-id='%d'>%s</a> for customer <a href='#' data-oe-model='%s' data-oe-id='%s'>%s</a>") % (
                     lead._name, lead.id, lead.name,
                     lead.partner_id.name, lead.partner_id.id,self.partner_name),
            date_deadline=self.date_follow_up)

    @api.multi
    def _create_opportunities(self):
        lead = self.sudo().env['crm.lead']
        for enquiry in self:
            if not enquiry.opportunity_ids:
                for type in enquiry.type_ids:
                    res = self._prepare_opportunities(type)
                    res.update(self._assign_enquiry_user(type))
                    print(res)
                    id = lead.create(res)
                    self._schedule_follow_up(id)
            else:
                print("Not creating Opportunities as they already exist")

    @api.multi
    def write(self, vals):
        return super(Enquiry, self).write(vals)

    def action_create_opportunities(self):
        self._create_opportunities(None)

    @api.multi
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
            'user_id': self.env.context.get('default_user_id') or self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'mobile': self.partner_mobile,
            'email': email_split[0] if email_split else False,
            'type': 'contact'
        }

    @api.model
    def _assign_enquiry_user(self, type):
        print("starting for " + type.name)
        user = self.env.user
        user_id = user.id
        user_team = self.sudo().env['crm.team'].search([('member_ids', '=', user.id)])
        user_team_type = user_team.team_type
        user_team_location = user_team.location_id
        if not user_team_type == type.team_type:
            if user_team_location:
                team = self.sudo().env['crm.team'].search([('location_id', 'child_of', user_team_location.id),
                                                           ('team_type', '=', type.team_type)], limit=1)
                print(team)
                if team and team.user_id:
                    return {'user_id': team.user_id.id,
                            'team_id': team.id
                            }
                else:
                    raise UserError(_("Error Assigning Sub Enquiry - Please check your team setup"))

        print(user_id)
        return {'user_id': user_id}
