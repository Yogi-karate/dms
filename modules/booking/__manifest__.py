# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'dms booking',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Handle Sales customization for DMS',
    'description': "Vehicle Dealership Business Domain",
    'depends': ['sale','dms'],
    'data': [
        'security/ir.model.access.csv',
        'views/booking_views.xml',
    ],
    'installable': True,
    'auto_install': False,

}
