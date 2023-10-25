# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Stock landed costs purchase auto",
    "version": "13.0.1.0.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/stock-logistics-workflow",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["stock_landed_costs", "purchase"],
    "data": [
    #"views/stock_landed_cost_view.xml",
    "views/purchase_order_view.xml",
    "views/product_product_view.xml",
    "views/reportes/pdf_presupuesto_report_call.xml",
    "views/reportes/pdf_presupuesto_report_template.xml",
    "views/stock_picking_view.xml",
    #'security/ir.model.access.csv',
    "views/purchaseline_order_view.xml",
    ],
    "installable": True,
}
