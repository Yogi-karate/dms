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


class Course(models.Model):
    _name = "course"
    _description = "Course"
    name = fields.Char(string='Name',required=True)
    seats = fields.Char('No of seats', required=True)
    hod = fields.Char(string='HOD')


    @api.model
    def create(self, vals):
        result = super(Course, self).create(vals)
        return result
