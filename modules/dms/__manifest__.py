# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'dms',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Handle Sales customization for DMS',
    'description': "Vehicle Dealership Business Domain",
    'depends': ['base_dms','purchase','crm_dms','vehicle','l10n_in'],
    'data': [
        'views/dms_views.xml',
        'views/crm_lead_views.xml',
        'security/dms_groups.xml',
        'security/ir.model.access.csv',
        'views/lead2oppor.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
