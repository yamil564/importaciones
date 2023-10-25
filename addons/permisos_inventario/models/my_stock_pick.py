#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


class stock_picking_v3(models.Model):#Picking
    _inherit = 'stock.picking'
    _order = 'id desc' #'min_date desc'

    descripcion_one = fields.Char(string="Prim. Descripcion")
    descripcion_two = fields.Char(string="Direccion",compute='_get_mercaderia')
    #vendedor_id = fields.Many2one('res.users', string='Vendedor', default=lambda self: self.env['sale.order'].search([('name', '=',self.group_id.name )]).user_id)
    mercaderia = fields.Char(compute='_get_mercaderia')
    nro_guia = fields.Char(compute='_get_nro_guia')
    tipo_vent = fields.Char()  #compute='_actualizar_movimient'
     
    def _get_mercaderia(self):
        for record in self:
            mercad = record.env['sale.order'].search([('name', '=',record.group_id.name )])
            record.mercaderia=mercad.mercaderia
            record.descripcion_two=mercad.partner_id.street
            #return mercaderia

    def _get_nro_guia(self):
        for record in self:
            nro = record.env['sale.order'].search([('name', '=',record.group_id.name )])
            record.nro_guia=nro.nro_guia

    '''def _actualizar_movimient(self):
        for record in self:
            nro = record.env['sale.order'].search([('name', '=',record.group_id.name )])
            if nro.tipo_vent=='Traslado entre almacen':
                if record.picking_type_id==4:
                    record.tipo_vent=nro.tipo_vent
                    record.picking_type_id=5
                    values= record.env['stock.picking'].search([('id', '=',record.id )])
                    values.update({'picking_type_id':5})
                    return values'''

    '''###@api.multi
    def write(self, vals):
        record = super(stock_picking_v3, self).write(vals)
        self._actualizar_movimient()
        return record'''

'''class stock_pack_operation_v3(models.Model):
    _inherit = 'stock.pack.operation'


    qty_done = fields.Float('Done', default=0.0, digits=dp.get_precision('Product Unit of Measure'), compute='_onchange_qty_done',inverse='_set_qty_done',store=True)
    
    
    ###@api.multi
    @api.depends('qty_done')
    def _onchange_qty_done(self):
        for record in self:
            record.qty_done = record.product_qty  #quitar done y campo realizado 

    def _set_qty_done(self):
        pass'''
    
