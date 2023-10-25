# -*- coding: utf-8 -*-
{
    'name': "Customizacion para Roatsa",
    'summary':
        """
        - Gastos adicionales en cotizacion.
        """,
    'description': """
        Modulo personalizado - Roatsa.
    """,
    'author': "KND S.A.C.",
    'website': "http://www.knd.pe",
    'category': 'Uncategorized',
    'version': '0.1',
    #'depends': ['base', 'sale', 'backend_theme_v13', 'web_responsive', 'report'],
    'depends': ['base', 'sale', 'backend_theme_v13', 'web_responsive','sales_team'],
    'data': [
        'views/sale_views.xml',
        'views/reporte_seguimiento_view.xml',
        'views/reportes/pdf_cotizacion_report_template.xml',
        'views/reportes/pdf_cotizacion_report_call.xml',
        'security/ir.model.access.csv'
    ],
}
