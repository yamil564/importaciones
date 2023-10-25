# -*- coding: utf-8 -*-
{
    'name': "reporte_importacion",

    'summary': """
        Reporte Importacion""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # son modulos para que funcionen de forma correcta
    # website para crear una web
    'depends': ['base','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/report.xml',
        'views/modif_compra.xml'
    ],
    # datos para que se pruebe como funciona el modulo
    'demo': [
        
    ],
}
