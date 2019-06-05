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


class VehicleLead(models.Model):
    _name = "vehicle.lead"
    _description = "Vehicle Lead"
    _inherit = ['crm.lead']
    vehicle_id = fields.Many2many('vehicle', string='Vehicle', track_visibility='onchange', track_sequence=1,
                                 index=True)

    @api.model
    def create(self, vals):
        result = super(VehicleLead, self).create(vals)
        return result
