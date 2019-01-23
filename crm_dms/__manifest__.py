# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': ' CRM DMS',
    'version': '1.0',
    'category': 'Base',
    'sequence': 60,
    'summary': 'DMS CRM Changes',
    'description': "Auto Dealership Business Domain",
    'depends': ['crm','dms'],
    'data': [
        'security/ir.model.access.csv',
        'views/dms_enquiry_views.xml',
        'views/crm_lead_views.xml',
        'data/mail_activity.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
