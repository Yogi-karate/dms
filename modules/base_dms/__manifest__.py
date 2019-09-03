# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Base DMS',
    'version': '1.0',
    'category': 'Base',
    'sequence': 60,
    'summary': 'DMS Base Changes',
    'description': "Auto Dealership Business Domain",
    'depends': ['base','l10n_in'],
    'data': [
        'views/res_partner_views.xml',
        'views/dms_menu_views.xml'
    ],
    'installable': True,
    'auto_install': True,
    'post_init_hook': 'post_init',
}
