# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'dms.config'

    def _init_settings(self):
        settings = {'lock_confirmed_po': True
        }
        res_config = self.sudo().env['res.config.settings'].set_values(settings)
