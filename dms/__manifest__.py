# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'dms',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Handle Sales customization for DMS',
    'description': "Vehicle Dealership Business Domain",
    'depends': ['base','sale','purchase','stock'],
    'data': [
        'views/dms_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
