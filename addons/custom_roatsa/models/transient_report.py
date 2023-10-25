#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


class reporteMovimientosTransient(models.Model):
    _name = "report.seguimiento.pedidos"
    _description = "Modelo transitorio para el reporte de seguimiento de entregas"

    order_number = fields.Char(string="Número de orden")
    order_date = fields.Char(string="Fecha")
    order_user = fields.Char(string="Vendedor")
    order_client = fields.Char(string="Cliente")
    order_address = fields.Char(string="Dirección")
    mov_number = fields.Char(string="Número de movimiento")
    state = fields.Char(string="Estado")
    nro_guia = fields.Char(string="Nro. Guia")

    def _compute_pedidos(self):
        # Elimina todos los datos anteriores almacenados en el reporte
        record_set = self.env['report.seguimiento.pedidos'].search([
        ])
        record_set.unlink()

        # Busca todas las órdenes de venta confirmadas (pedidos de ventas)
        orders = self.env["sale.order"].search([["state", "=", "sale"]])

        for order in orders:
            # Declaración de variables a utilizar
            entrega = 1
            paquete = 1
            almacen = 1
            vals = {}

            # Para evitar problemas con movimientos anteriores al flujo en 3
            # etapas, solamente seleccionamos las órdenes de venta que tengan
            # 3 o más movimientos de almacén

            if len(order.picking_ids) >= 3:
                # Asignamos cada movimiento a una variable según el tipo de
                # movimiento que sea (PICK, PACK, OUT)
                '''for p in order.picking_ids:
                    if p.picking_type_id.name == "Delivery Orders":
                        entrega = p
                    if p.picking_type_id.name == "Pack":
                        paquete = p
                    if p.picking_type_id.name == "Pick":
                        almacen = p'''
                for p in order.picking_ids:
                    if p.picking_type_id.id == 4:#p.picking_type_id.name == "Delivery Orders":
                        entrega = p
                    if p.picking_type_id.id == 2:#p.picking_type_id.name == "Pack":
                        paquete = p
                    if p.picking_type_id.id == 3: #p.picking_type_id.name == "Pick":
                        almacen = p
                    #raise Warning(_(p.picking_type_id.id))
                # Si tenemos todas las variables asignadas con valores
                # diferentes al que se le dió inicialmente procedemos a crear
                # las líneas del reporte
                #print("line 54")
                #print(entrega)
                #print(paquete)
                #print(almacen)
                if order.partner_id.parent_id.name:
                    nom_cliente=order.partner_id.parent_id.name #+', '+ order.partner_id.name
                else:
                    nom_cliente=order.partner_id.name
                if entrega != 1 and paquete != 1 and almacen != 1:

                    if almacen.state == 'assigned':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'nro_guia': order.nro_guia,
                            'order_client': nom_cliente,
                            'order_address': order.partner_id.street,
                            'mov_number': almacen.name,
                            'state': 'En almacén'
                        }
                        #print(vals)
                    elif paquete.state == 'assigned' and entrega.state == 'waiting':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'nro_guia': order.nro_guia,
                            'order_client': nom_cliente,
                            'order_address': order.partner_id.street,
                            'mov_number': paquete.name,
                            'state': 'Listo para despachar'
                        }
                        #print(vals)
                    elif entrega.state == 'assigned':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'nro_guia': order.nro_guia,
                            'order_client': nom_cliente,
                            'order_address': order.partner_id.street,
                            'mov_number': entrega.name,
                            'state': 'En tránsito'
                        }
                        #print(vals)
                    elif entrega.state == 'done':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'nro_guia': order.nro_guia,
                            'order_client': nom_cliente,
                            'order_address': order.partner_id.street,
                            'mov_number': entrega.name,
                            'state': 'Entregado'
                        }
                        #print(vals)

                # Si los datos coinciden con alguna de las validaciones y se
                # generaron datos para registrar, procedemos a crear
                if vals:
                    #print("existe vals")
                    self.sudo().create(vals)



class stock_picking_v2(models.Model):#Picking
    _inherit = 'stock.picking'

    ###@api.multi
    def do_new_transfer(self):
        res = super(stock_picking_v2, self).do_new_transfer()
        if self.picking_type_id.name!='Recepciones':
            res = self.env['report.seguimiento.pedidos']._compute_pedidos()
        #account_reconcile_model_lines = self.env['account.reconcile.model.line.template'].search([
        #    ('model_id', '=', account_reconcile_model.id)
        #])
        if self.picking_type_id.name=='Transferencias internas':
            vals = {
                    'location_id': 15,#Almacen
                    'partner_id': self.partner_id.id,
                    'location_dest_id': 12,#Despacho
                    'origin': self.name,
                    'picking_type_id': 3,#Pick
                    'state': 'draft',
                    'move_lines': [(0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'uom.uom': line.uom.uom.id,
                        'name': line.product_id.name
                        }) for line in self.move_lines]
                    }
            res=self.env['stock.picking'].create(vals)
            vals2 = {
                    'location_id': 12,#Despacho
                    'partner_id': self.partner_id.id,
                    'location_dest_id': 16,#Salida
                    'origin': self.name,
                    'picking_type_id': 2,#id Pack
                    'state': 'draft',
                    'move_lines': [(0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'uom.uom': line.uom.uom.id,
                        'name': line.product_id.name
                        }) for line in self.move_lines]
                    }
            res=self.env['stock.picking'].create(vals2)
            vals3 = {
                    'location_id': 16,# id Salida
                    'partner_id': self.partner_id.id,
                    'location_dest_id': 15, #22 Ubicaciones de empresas cliente(ventas) - almacen 2 existencias
                    'origin': self.name,
                    'picking_type_id': 4,#Out ordenes de entrega
                    'state': 'draft',
                    'move_lines': [(0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'uom.uom': line.uom.uom.id,
                        'name': line.product_id.name
                        }) for line in self.move_lines]
                    }
            res=self.env['stock.picking'].create(vals3)
        
        return res
    '''
    ###@api.multi
    def do_new_transfer(self):
        res = super(stock_picking_v2, self).do_new_transfer()
        #record_set = self.env['report.seguimiento.pedidos']
        #record_set._compute_pedidos()
        record_set = self.env['report.seguimiento.pedidos'].search([
        ])
        record_set.unlink()

        # Busca todas las órdenes de venta confirmadas (pedidos de ventas)
        orders = self.env["sale.order"].search([["state", "=", "sale"]])
        
        for order in orders:
            # Declaración de variables a utilizar
            entrega = 1
            paquete = 1
            almacen = 1
            vals = {}

            # Para evitar problemas con movimientos anteriores al flujo en 3
            # etapas, solamente seleccionamos las órdenes de venta que tengan
            # 3 o más movimientos de almacén
            #raise Warning(_('Pasa a for'))
        
            if len(order.picking_ids) >= 3:
                # Asignamos cada movimiento a una variable según el tipo de
                # movimiento que sea (PICK, PACK, OUT)
                #raise Warning(_('Pasa a ifs mayor 3'))
                for p in order.picking_ids:
                    if p.picking_type_id.id == 4:#p.picking_type_id.name == "Delivery Orders":
                        entrega = p
                    if p.picking_type_id.id == 2:#p.picking_type_id.name == "Pack":
                        paquete = p
                    if p.picking_type_id.id == 3: #p.picking_type_id.name == "Pick":
                        almacen = p
                    #raise Warning(_(p.picking_type_id.id))

                # Si tenemos todas las variables asignadas con valores
                # diferentes al que se le dió inicialmente procedemos a crear
                # las líneas del reporte
                print("line 54")
                print(entrega)
                print(paquete)
                print(almacen)
                #raise Warning(_(paquete))
                if entrega != 1 and paquete != 1 and almacen != 1:
                    #raise Warning(_('ingresa if existe'))
                    if almacen.state == 'assigned':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'order_client': order.partner_id.name,
                            'order_address': order.partner_id.street,
                            'mov_number': almacen.name,
                            'state': 'En almacén'
                        }
                        print(vals)
                    elif paquete.state == 'assigned' and entrega.state == 'waiting':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'order_client': order.partner_id.name,
                            'order_address': order.partner_id.street,
                            'mov_number': paquete.name,
                            'state': 'Listo para despachar'
                        }
                        print(vals)
                    elif entrega.state == 'assigned':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'order_client': order.partner_id.name,
                            'order_address': order.partner_id.street,
                            'mov_number': entrega.name,
                            'state': 'En tránsito'
                        }
                        print(vals)
                    elif entrega.state == 'done':
                        vals = {
                            'order_number': order.name,
                            'order_date': order.confirmation_date,
                            'order_user': order.user_id.name,
                            'order_client': order.partner_id.name,
                            'order_address': order.partner_id.street,
                            'mov_number': entrega.name,
                            'state': 'Entregado'
                        }
                        print(vals)

                # Si los datos coinciden con alguna de las validaciones y se
                # generaron datos para registrar, procedemos a crear
                if vals:
                    print("existe vals")
                    #self.sudo().create(vals)
                    self.env['report.seguimiento.pedidos'].create(vals)
        return res
    '''

#class sale_order_v2(models.Model):#Picking
    #_inherit = 'sale.order'

    
    ####@api.multi
    #def action_confirm(self):
        #res = super(sale_order_v2, self).action_confirm()
        #res = self.env['report.seguimiento.pedidos']._compute_pedidos()
        #res
        
        #return res
    