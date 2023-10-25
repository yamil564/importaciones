#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


class componentes_lista_materiales(models.Model):#Picking
    _inherit = 'mrp.bom.line'

    lst_price= fields.Float(string="Precio",compute='_get_precio',inverse='_set_precio',store=True)
    charprice = fields.Float(string="Precio2",compute='_get_precio2',inverse='_set_precio2')
    price3 = fields.Float(related="product_id.lst_price", string="precio 3", store=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    price_discount = fields.Float(compute='_get_price_discount', string='SubTotal', readonly=True)

    ###@api.one
    @api.depends('product_id')
    def _get_precio2(self):
        for prod_tml in self: 
            producto = self.env['product.product'].search([('product_tmpl_id.id', '=', prod_tml.product_id.product_tmpl_id.id)])
            self.charprice=producto.lst_price
            if producto.id:
                sql = "update mrp_bom_line set lst_price=%s where product_id=%s" % (producto.lst_price,producto.id)
                self._cr.execute(sql)
            
    ###@api.one
    @api.depends('product_id')
    def _get_precio(self):
        self.lst_price = self.product_id.lst_price
    
    def _set_precio(self):
        pass
    def _set_precio2(self):
        pass

    '''@api.onchange('charprice')
    def cambio_precio(self):
        self.lst_price = self.charprice'''

    '''def _actualizar_precio(self):
        values = self.env['mrp.bom.line'].search([('id', '=', self.id)])
        values.update({'lst_price': values.charprice })
        return values

    ###@api.multi
    def write(self, vals):
        record = super(componentes_lista_materiales, self).write(vals)
        self._actualizar_precio()
        return record'''

    @api.depends('lst_price', 'discount','product_qty')
    def _get_price_discount(self):
        for line in self:
            line.price_discount = (line.product_qty*line.lst_price) * (1.0 - line.discount / 100.0)


class lista_materiales(models.Model):#Picking
    _inherit = 'mrp.bom'

    amount_total = fields.Float(compute='_compute_total_compo',string='Total:', default=0.0)
    type = fields.Selection([
        ('normal', 'Fabricar este producto'),
        ('phantom', 'Enviar este producto como un conjunto de componentes (kit)')], 'Tipo de LdM',
        default='phantom', required=True,
        help="Kit (Phantom): When processing a sales order for this product, the delivery order will contain the raw materials, instead of the finished product.")
    
    ###@api.one
    @api.depends('bom_line_ids.price_discount')
    def _compute_total_compo(self):
        for record in self:
            record.amount_total += sum([line.price_discount for line in record.bom_line_ids])
            #record.product_tmpl_id.list_price= record.amount_total

    def _actualizar_precio(self):
        values = self.env['product.product'].search([('product_tmpl_id.id', '=', self.product_tmpl_id.id)])
        
        values.update({'lst_price': values.price_materiales })
        return values

    def _actualizar_precio_template(self):
        values = self.env['product.template'].search([('id', '=', self.product_tmpl_id.id)])
        
        values.update({'list_price': values.price_materiales })
        return values

    @api.model
    def create(self, vals):
        record = super(lista_materiales, self).create(vals)
        record._actualizar_precio()
        record._actualizar_precio_template()
        return record

    ###@api.multi
    def write(self, vals):
        record = super(lista_materiales, self).write(vals)
        self._actualizar_precio()
        self._actualizar_precio_template()
        return record

    ###@api.multi
    def unlink(self):
        record = super(lista_materiales, self).unlink()
        
        return True

    
        
class product_template_v3(models.Model):#Picking
    _inherit = 'product.template'
    
    price_materiales = fields.Float(string='Precio del Material:',compute='_get_list_price')
    
    @api.depends('list_price')
    def _get_list_price(self):
        for record in self:
            record.price_materiales = 0
            if record.id:
                price = self.env['mrp.bom'].search([('product_tmpl_id.id', '=',record.id )])
                record.price_materiales += sum([line.amount_total for line in price])
    

class product_templatev4(models.Model):
    _inherit = 'product.template'

    service_to_purchase = fields.Char("Servicio a comprar")

class product_product_v3(models.Model):#Picking
    _inherit = 'product.product'
    
    price_materiales = fields.Float(string='Precio del Material:',compute='_get_list_price')
    
    @api.depends('lst_price')
    def _get_list_price(self):
        for record in self:
            record.price_materiales = 0
            if record.id:
                price = self.env['mrp.bom'].search([('product_tmpl_id.id', '=',record.product_tmpl_id.id )])
                record.price_materiales += sum([line.amount_total for line in price])
