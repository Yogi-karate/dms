# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from babel.dates import format_date
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class CrmTeam(models.Model):
    _name = "crm.team"
    _inherit = 'crm.team'

    manager_user_ids = fields.Many2many(
        'res.users', 'team_manager_user_rel', 'team_id', 'user_id',
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_manager').id)],
        string='Managers')
    location_id = fields.Many2one('stock.location', domain=[('usage', '=', 'Sales')], string='Sales Team Location')
    team_type = fields.Selection(
        [('sales', 'Sales'), ('insurance', 'Insurance'), ('finance', 'Finance'), ('service', 'Service'),
         ('business-center', 'Business-Center'),('website', 'Website')], string='Team Type', default='sales',
        required=True,
        help="The type of this channel, it will define the resources this channel uses.")
