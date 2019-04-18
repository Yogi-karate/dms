# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': ' CRM DMS',
    'version': '1.0',
    'category': 'Base',
    'sequence': 60,
    'summary': 'DMS CRM Changes',
    'description': "Auto Dealership Business Domain",
    'depends': ['crm','sale_dms'],
    'data': [
        'security/ir.model.access.csv',
        'security/dms_enquiry_security.xml',
        'views/dms_enquiry_views.xml',
        'data/crm_stage_data.xml',
        'data/mail_activity.xml',
        'data/product_category_data.xml',
        'data/sale_team_data.xml',
        'data/opportunity_type_data.xml',
        'data/lead_cron_data.xml',
        'wizard/dms_enquiry_to_quotation_views.xml',
        'wizard/dms_enquiry_assign_views.xml',
        'report/enquiry_report_views.xml',
        'report/performance_report_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
