#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

from odoo import http, tools
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.lru import LRU



class pdf_presupuesto_report(models.AbstractModel):
    _name = 'report.personalizacion_compras.pdf_presupuesto_template'

    @api.model
    def render_html(self, docids, data=None):
        presupuesto = self.env['purchase.order'].sudo().browse(docids)
        docargs = {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'docs': presupuesto,
            'data': data,
        }
        return self.env['report'].sudo().render('personalizacion_compras.pdf_presupuesto_template', docargs)


class pdf_presupuesto_report(models.AbstractModel):
    _name = 'report.personalizacion_compras.pdf_presupuesto_proov_template'

    @api.model
    def render_html(self, docids, data=None):
        self.clear_caches()
        num=int(docids[0])
        presupuesto = self.env['purchase.order'].browse(num)
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'purchase.order',
            'docs': presupuesto,
            'data': data,
            'datetime': datetime
        }
        return self.env['report'].sudo().render('personalizacion_compras.pdf_presupuesto_proov_template', docargs)

    