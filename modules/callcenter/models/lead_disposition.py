from odoo import api, fields, models, _


class LeadDisposition(models.Model):
    _description = 'Lead Disposition'
    _name = 'dms.lead.disposition'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
