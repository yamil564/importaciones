#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, models


class pdf_landed_cost_report(models.AbstractModel):
    _name = 'report.stock_landed_costs_purchase_auto.pdf_landed_cost_template'

    @api.model
    def render_html(self, docids, data=None):
        company = self.env['res.company'].browse(1)
        presupuesto = self.env['stock.landed.cost'].browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'stock.landed.cost',
            'docs': presupuesto,
            'data': data,
            'company': company
        }#
        return self.env['report'].render('stock_landed_costs_purchase_auto.pdf_landed_cost_template', docargs)
