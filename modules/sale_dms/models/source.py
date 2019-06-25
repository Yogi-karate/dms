# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class Source(models.Model):
    _name = 'utm.source'
    _inherit = 'utm.source'
    active = fields.Boolean(string='Active',default=True)
    medium = fields.Many2one('utm.medium',string='Medium',required=True)
    campaign = fields.Many2one('utm.campaign',string='Campaign')

    @api.model
    def create(self,vals):
        print(vals)
        medium_name = self.env['utm.medium'].browse(vals['medium']).name
        campaign_name = self.env['utm.campaign'].browse(vals['campaign']).name
        if campaign_name:
            mod_name = vals['name'] + '/' + medium_name + '/' + campaign_name
        else:
            mod_name = vals['name'] + '/' + medium_name
        vals2 = {
            'name': mod_name,
            'medium': vals['medium'],
            'campaign': vals['campaign']
        }
        res = super(Source, self).create(vals2)
        return res

    @api.multi
    def write(self, vals):
        print(vals)
        if 'name' not in vals:
            vals['name'] = self.name
        if 'medium' not in vals:
            vals['medium'] = self.medium.id
            medium_name = self.medium.name
        else:
            medium_name = self.env['utm.medium'].browse(vals['medium']).name
        if 'campaign' not in vals:
            vals['campaign'] = self.campaign.id
            campaign_name = self.campaign.name
            if not self.campaign.id:
                campaign_name = ''
        else:
            campaign_name = self.env['utm.campaign'].browse(vals['campaign']).name
        mod_name = vals['name'] + '/' + medium_name + '/' + campaign_name
        vals2 = {
            'name': mod_name,
            'medium': vals['medium'],
            'campaign': vals['campaign']
        }
        res = super(Source, self).write(vals2)
        return res




