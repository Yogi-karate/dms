# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'callcenter',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Handle Sales customization for DMS',
    'description': "Vehicle Dealership Business Domain",
    'depends': ['crm_dms','vehicle'],
    'data': [
        'security/callcenter_groups.xml',
        'security/ir.model.access.csv',
        'data/mail_activity.xml',
        'data/opportunity_type_data.xml',
        'wizard/dms_vehicle_lead_assign.xml',
        'wizard/dms_lead_lost.xml',
        'wizard/lead_to_opportunity.xml',
        'views/booking_insurance.xml',
        'views/booking_service.xml',
        'views/activity_done_views.xml',
        'views/crm_lead_views.xml',
        'views/dms_vehicle_lost_views.xml',
        'views/callcenter_views.xml',
        'data/service_lead_cron_data.xml',
        'data/vehicle_import_cron_data.xml',


    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}
