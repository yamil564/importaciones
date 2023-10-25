# -*- coding: utf-8 -*-
{
    'name': "metodo_costo",

    'summary': """
        Metodo costo""",

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
    'depends': ['base','stock_landed_costs'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    # datos para que se pruebe como funciona el modulo
    'demo': [
        
    ],
}
