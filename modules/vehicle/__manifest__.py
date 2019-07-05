# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Vehicle',
    'version': '1.0',
    'category': 'Products',
    'sequence': 60,
    'summary': 'Handle Vehicles for DMS',
    'description': "Vehicle Business Domain",
    'depends': ['base_dms','sale_dms','stock'],
    'data': [
        'security/vehicle_security.xml',
        'security/ir.model.access.csv',
        'views/vehicle_views.xml',
        'views/stock_picking_views.xml',
        'views/vehicle_customer_views.xml',

    ],
    'installable': True,
    'auto_install': True,

}
