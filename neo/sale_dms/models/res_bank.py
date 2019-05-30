import re

import collections

from odoo import api, fields, models, _


class Bank(models.Model):
    _name = 'res.partner.bank'
    _description = 'Bank Accounts'
    _inherit = 'res.partner.bank'
    ifsc = fields.Char('IFSC Code', index=True, help="ifsc.", store=True)
