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
        'security/dms_groups.xml',
        'security/ir.model.access.csv',
        'views/dms_views.xml',
        'views/booking_service.xml',
        'views/activity_done_views.xml',
        'data/opportunity_type_data.xml',
        'wizard/lead_to_opportunity.xml',
        'views/crm_lead_views.xml',
        'data/service_lead_cron_data.xml',
        'data/vehicle_import_cron_data.xml',
        'wizard/dms_vehicle_lead_assign.xml',
        'views/dms_vehicle_lost_views.xml',
        'views/booking_insurance.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
