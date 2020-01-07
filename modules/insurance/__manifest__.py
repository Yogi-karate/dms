# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': ' Insurance_DMS',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Insurance Module',
    'depends': ['vehicle'],
    'description': "Insurance Module",
    'data': [
        'security/ir.model.access.csv',
        'views/insurance_schedule_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}