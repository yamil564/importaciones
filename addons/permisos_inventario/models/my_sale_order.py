#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import time
import logging


class sale_order_v4(models.Model):
    _inherit = 'sale.order'

    ratio_actual = fields.Float(string="Cambio", compute="_compute_get_cambio")
    amount_total_dolar = fields.Float(compute="_compute_get_cambio",store=True,string="Total $")
    amount_total_dolar2 = fields.Float(string="Total $",compute="_compute_get_cambio")
    @api.depends('amount_total','ratio_actual')
    def _compute_get_cambio(self): 
        for record in self:
            fecha1=record.date_order
            fecha=datetime.strptime(str(fecha1),'%Y-%m-%d %H:%M:%S').date()
            ratio_actual=self.env['res.currency.rate'].search([('currency_id.id','=',record.currency_id.id),('name','>=',fecha)], limit=1, order='name asc').rate 
            record.ratio_actual=ratio_actual
            if record.ratio_actual!=0:
                record.amount_total_dolar=ratio_actual*record.amount_total
                record.amount_total_dolar2=record.ratio_actual*record.amount_total
            else:
                record.amount_total_dolar2=record.amount_total
                record.amount_total_dolar=record.amount_total

    ####@api.multi
    def action_confirm(self):
        res = super(sale_order_v4, self).action_confirm()
        for record in self:
            record.estado_ganado='Ganado'
        return res

    estado_ganado = fields.Selection([('Ganado', 'Ganado'),('Perdido', 'Perdido'),('Negociando', 'Negociando')],string="Estado",default='Negociando')
    ganado_estado = fields.Char()
    mercaderia = fields.Selection([('Por recoger', 'Por recoger'),('Para enviar', 'Para enviar'),('Por definir', 'Por definir')])
    nro_guia = fields.Char(string="Nro. Guia")   
    tipo_vent = fields.Selection([('Venta', 'Venta'),('Traslado entre almacen', 'Traslado entre almacen')],default='Venta')
    vat_partner = fields.Char(compute='_get_vat_partner')
    vat_partner3 = fields.Char(compute='_get_vat_client')
    boolean_cliente = fields.Boolean(compute='_get_vat_client')
    vat_partner4 = fields.Char(compute='_get_vat_client',default='0')
    sim_igual = fields.Char(compute='_get_vat_client',default='!=',inverse='_set_vat_client', copy=False)
    vat_partner2 = fields.Char(compute='_get_vat_client')

    ####@api.multi
    @api.depends('user_id')
    def _nro_usuario(self):
        return str(self.env.user.id)
    nro_user = fields.Char(default=_nro_usuario)

    @api.depends('user_id')
    def _default_almacen(self):
        if self.env.user.sede.almacen.id:
            return self.env['stock.warehouse'].search([('id', '=', self.env.user.sede.almacen.id)]).id
        else:
            return self.env['stock.warehouse'].search([('id', '=', 1)]).id
    warehouse_id=fields.Many2one('stock.warehouse', string='Almacen2', default=_default_almacen)

    def _actualizar_precio(self):
        if self.tipo_vent=='Traslado entre almacen':
            values = self.env['sale.order.line'].search([('order_id.id', '=', self.id)])
            values.update({'price_unit': 0.00, 'tipo_vent':'Traslado entre almacen','tipo_vent2':True})
            return values
        else:
            values = self.env['sale.order.line'].search([('order_id.id', '=', self.id)])
            values.update({'tipo_vent':'Venta','tipo_vent2':False})
            return values

    ####@api.multi
    def write(self, vals):
        record = super(sale_order_v4, self).write(vals)
        self._actualizar_precio()
        return record

    def _get_vat_partner(self):
        for record in self:
            record.vat_partner = record.partner_id.id

    def _set_vat_client(self):
        pass

    ####@api.multi
    @api.depends('partner_id')
    def _get_vat_client(self):
        #for record in self:
        if self.state=='draft':
            self.vat_partner4='0'
            self.sim_igual='!='
            self.vat_partner2=self.partner_id.street 
        else:
            self.vat_partner3 = self.partner_id.parent_id.id
            if self.partner_id.id:
                if self.vat_partner3 :
                    self.boolean_cliente=True
                    self.vat_partner4 = self.partner_id.parent_id.id
                    self.sim_igual ='='
                    self.vat_partner2=self.partner_id.street
                else:
                    self.boolean_cliente=False
                    self.vat_partner4 = self.partner_id.id
                    self.sim_igual ='='
                    self.vat_partner2=self.partner_id.street
    

class sale_order_line_v4(models.Model):
    _inherit = 'sale.order.line'

    tipo_vent = fields.Selection([('Venta', 'Venta'),('Traslado entre almacen', 'Traslado entre almacen')],default='Venta')
    tipo_vent2 = fields.Boolean(default=False)
    ####@api.multi
    def _get_dominio_product(self):
        #for record in self:
        '''if self.env.user.sede.almacen.id:
            almacen=self.env['stock.warehouse'].search([('id', '=', self.env.user.sede.almacen.id)]).id
            ubicacion=almacen.lot_stock_id.id
        else:
            almacen=self.env['stock.warehouse'].search([('id', '=', 1)]).id
            ubicacion=almacen.lot_stock_id.id
        self.env['stock.quant'].search([('location_id', '=', ubicacion),('product_id', '=', self.id)])'''
        #al agregar un nuevo almacen agregar otro if con el id del otro usuario y retornar tercero
        if str(self.env.user.id)=='19':#cambiar id
            return 'Segundo'
        else:
            return 'No'#[Si,No]
    dom_segundo_almacen = fields.Char(default=_get_dominio_product)
    

class product_product_v2(models.Model):
    _inherit = 'product.product'

    segundo_almacen = fields.Char(default='No')

    ####@api.multi
    def actualizar_seg_almacen(self):
        #al agregar un nuevo almacen agregar otro if con el id de la locacion
        orders = self.env["product.product"].search([["sale_ok", "=", True]])
        for record in orders:
            if self.env['stock.quant'].search([('location_id', '=', 22),('product_id', '=', record.id)]):#cambiar id
                vals ={'segundo_almacen': 'Segundo'}
                record.write(vals)
            else:
                vals ={'segundo_almacen': 'No'}
                record.write(vals)
    
class product_template_v2(models.Model):
    _inherit = 'product.template'

    segundo_almacen = fields.Char(default='No')

    ####@api.multi
    def actualizar_seg_almacen(self):
        orders = self.env["product.template"].search([["sale_ok", "=", True]])
        for record in orders:
            if self.env['stock.quant'].search([('location_id', '=', 22),('product_id.product_tmpl_id', '=', record.id)]):#cambiar id
                vals ={'segundo_almacen': 'Segundo'}
                record.write(vals)
            else:
                vals ={'segundo_almacen': 'No'}
                record.write(vals)
    