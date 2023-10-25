# -*- coding: utf-8 -*-
{
    'name': "Personalizacion Compras",
    'summary':
        """
        Personalizacion compras
        """,
    'description': """
        Personalizacion compras
    """,
    'author': "KND S.A.C.",
    'website': "http://www.knd.pe",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['purchase','stock_landed_costs_purchase_auto'],
    'data': [
        'view/my_compras.xml',
        'view/reportes/pdf_presupuesto_report_template.xml',
        'view/reportes/pdf_presupuesto_report_proov_template.xml',
        'view/reportes/pdf_presupuesto_report_call.xml'
    ],
    'installable': True,
    'active': True,
    'application': True,
}
#