# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError


class Digest(models.Model):
    _name = 'dms.lead.digest'
    _description = 'Lead Counts for user'

    opportunities_count = fields.Integer(
        compute='_compute_opportunities',
        string='Number of open opportunities', readonly=True)

    def _compute_opportunities(self):
        opportunity_data = self.env['crm.lead'].read_group([
            ('probability', '=', 100),
            ('type', '=', 'opportunity'),
        ], ['name', 'activity_state', 'stage_id'], ['stage_id'])
        counts = {datum['stage_id'][0]: datum['stage_id_count'] for datum in opportunity_data}
        for digest in self:
            digest.opportunities_count = counts.get(team.id, 0)
