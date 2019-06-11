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


class Qualification(models.Model):
    _name = "qualification"
    _description = "Qualification"
    year = fields.Char(string='year')
    address = fields.Char('College Name,Place')
    percentage = fields.Char('Percentage')
    medium = fields.Char('Medium')
    qualification = fields.Selection([
        ('tenth', '10th'),
        ('tenplus', '10 + 2'),
        ('degree', 'Degree/Courses'),
    ], string='Qualification')

    @api.model
    def create(self, vals):
        result = super(Qualification, self).create(vals)
        return result