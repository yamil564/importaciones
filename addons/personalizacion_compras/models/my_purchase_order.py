#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


class purchase_order_v1(models.Model):
    _inherit = 'purchase.order'

    cliente = fields.Many2one('res.partner', 'Para:')
    autorizado_por = fields.Many2one('res.users', 'Autorizado Por')
    verificado_por = fields.Many2one('res.users', 'Verificado Por')
    tipo_pago = fields.Selection([('Total','100%'),('Parcial','Parcial')],string='Pagos al:')
    
    archivo_guia = fields.Binary()
    archivo_factura = fields.Binary()
    archivo_transferencia = fields.Binary()
    archivo_extra = fields.Binary()

    note = fields.Char(string='Note')
    port = fields.Char(string='Port')
    delivery_time = fields.Date(string='Delivery Time')
    payment_terms = fields.Char(string='Payment Terms')

    #@api.multi
    def print_quotation(self):
        #self.write({'state': "sent"})
        return self.env['report'].get_action(self, 'purchase.report_purchasequotation')
        #return self.env['report'].get_action(self, 'personalizacion_compras.pdf_presupuesto_proov_template')