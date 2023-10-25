# -*- coding: utf-8 -*-
#, 'report_xlsx' falta
#https://apps.odoo.com/apps/modules/10.0/stock_transport_management/
{
    'name': "Stock Transport",
    'version': '10.0.2.0.0',
    'summary': """Manage Stock Transport Management With Ease""",
    'description': """This Module Manage Transport Management Of Stocks""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Warehouse',
    'depends': ['sale', 'stock'],
    'data': [
        'views/transport_vehicle_view.xml',
        'views/transport_transportista_view.xml',
        'views/transport_sale_view.xml',
        'views/transport_stock_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
