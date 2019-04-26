# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'dms sale',
    'version': '1.0',
    'category': 'Sale',
    'sequence': 60,
    'summary': 'Handle Sales customization for DMS',
    'description': "Vehicle Dealership Business Domain",
    'depends': ['sale_management'],
    'data': [
        'views/sale_views.xml',
        'views/crm_team_views.xml',
        'views/pricelist_views.xml',
        'views/create_product_variant.xml',
        'views/dms_pricelist_views.xml',
        'views/res_bank_views.xml',
        'report/pdf_report_templates.xml',
        'security/sale_security.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': True,

}
