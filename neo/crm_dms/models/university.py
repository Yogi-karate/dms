from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode


class University(models.Model):
    _name = "university"
    _description = "University"
    name = fields.Char(string='Name')
    address = fields.Char('address',required=True)
    mobile = fields.Char('MOBILE',required=True)
    course = fields.Many2many('course', required=True)

    @api.model
    def create(self, vals):
        result = super(University, self).create(vals)
        return result
