# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': ' Service_DMS',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Service Module',
    'description': "Service Module",
    'depends': ['callcenter'],
    'data': [
        'security/service_security.xml',
        'security/ir.model.access.csv',
    ],
'installable': True,
    'auto_install': False,
    'application': True,
}