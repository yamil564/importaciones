#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from re import I
#from odoo import fields, models, api
import re
from odoo.exceptions import ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import odoo.addons.decimal_precision as dp
import time

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ratio_actual = fields.Float(string="Cambio", compute="_compute_get_cambio")
    incoterm_id = fields.Many2one(string='Incoterm',comodel_name='account.incoterms')
    landed_cost_number = fields.Integer(compute="_compute_landed_cost_number")
    amount_total_dolar = fields.Float(compute="_compute_get_cambio",store=True,string="Total $")#amount_total
    amount_total_dolar2 = fields.Float(string="Total $",compute="_compute_get_cambio")
    tipo_compra_le = fields.Selection([
        ('Local','Compra Local'),
        ('Importacion','Importacion')
        ], string="Tipo compra")
    
    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        if res.tipo_compra_le == 'Local':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.local') or '/'
            res.update({'name':vals['name']})
        return res

    @api.depends('amount_total','ratio_actual')
    def _compute_get_cambio(self): 
        for record in self:
            fecha1=record.date_order
            fecha1=str(fecha1)
            fecha=datetime.strptime(fecha1,'%Y-%m-%d %H:%M:%S')
            ratio_actual=self.env['res.currency.rate'].search([('currency_id.id','=',record.currency_id.id),('name','>=',fecha1[:10]+' '+'00:00:00')], limit=1, order='name asc').rate 
            record.ratio_actual=ratio_actual
            if record.ratio_actual!=0:
                record.amount_total_dolar=ratio_actual*record.amount_total
                record.amount_total_dolar2=record.ratio_actual*record.amount_total
            else:
                record.amount_total_dolar2=record.amount_total
                record.amount_total_dolar=record.amount_total

    def _compute_landed_cost_number(self): 
        for record in self:
            if record.state=='draft':
                record.landed_cost_number = 0
            else:
                record.landed_cost_number = 1

    def action_view_stock_landed_cost(self):
        action = self.env.ref("stock_landed_costs.action_stock_landed_cost").read()[0]
        action["context"] = {"search_default_names_purchase_ids": self.name}
        return action

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    saldo_pendiente = fields.Integer(compute="_compute_saldo_pendiente",store=True)
    saldo_pendiente2 = fields.Integer(compute="_compute_saldo_pendiente")
    observacion = fields.Char(string='Observacion')
    codigo_producto = fields.Char(compute="_compute_codigo_producto",store=True,string='Código de proveedor')
    default_code = fields.Char(compute="_compute_codigo_producto")
    description_purchase = fields.Char(compute="_compute_codigo_producto")
    codigo_producto2 = fields.Char(compute="_compute_codigo_producto")
    tipo_compra_le = fields.Selection([
        ('Local','Compra Local'),
        ('Importacion','Importacion')
        ], string="Tipo compra",compute="_compute_tipo_compra")

    @api.depends('order_id')
    def _compute_tipo_compra(self): 
        for record in self:
            record.tipo_compra_le = record.order_id.tipo_compra_le

    @api.depends('qty_received', 'product_qty')
    def _compute_saldo_pendiente(self): 
        for record in self:
            record.saldo_pendiente = record.product_qty -record.qty_received
            record.saldo_pendiente2 = record.product_qty -record.qty_received

    @api.depends('product_id')
    def _compute_codigo_producto(self): 
        for record in self:
            record.codigo_producto = record.product_id.codigo_purchase
            record.codigo_producto2 = record.product_id.codigo_purchase
            record.description_purchase = record.product_id.description_purchase
            record.default_code = record.product_id.default_code
        
    
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.display_name
        if product_lang.description_purchase:
            #self.name += '\n' + product_lang.description_purchase
            name = product_lang.description_purchase
            if product_lang.codigo_purchase:
                name = product_lang.codigo_purchase+' '+product_lang.description_purchase
        if product_lang.codigo_purchase:
            name = product_lang.codigo_purchase
            if product_lang.description_purchase:
                name = product_lang.codigo_purchase+' '+product_lang.description_purchase

        '''if self.order_id.tipo_compra_le=='Local':
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
                self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
            else:
                self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)'''

        return name

    