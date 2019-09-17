
from odoo import api, fields, models, _


class InsuranceCompany(models.Model):
    _description = 'Insurance Company'
    _name = 'res.insurance.company'
    _inherit = 'res.bank'
    _order = 'name'