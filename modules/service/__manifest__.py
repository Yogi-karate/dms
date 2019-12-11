# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': ' Service_DMS',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Service Module',
    'depends': ['vehicle'],
    'description': "Service Module",
    'data': [
        'security/service_security.xml',
        'security/ir.model.access.csv',
        'views/service_type_views.xml',
        'views/service_schedule_views.xml',
    ],
'installable': True,
    'auto_install': False,
    'application': True,
}