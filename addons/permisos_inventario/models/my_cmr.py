#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta
import odoo.addons.decimal_precision as dp
import logging
import time


class crm_lead_v1(models.Model):
    _inherit = 'crm.lead'
    #_order = 'id desc'

    prueba = fields.Char(string="Prueba")
    #totalCotizacion = fields.Monetary(string="Total",compute='_get_totalCotizacion')
    totalcotizacion = fields.Float(string="Total",compute='_get_totalCotizacion', compute_sudo=True, store=True)
    date_deadline = fields.Date(string='Cierre previsto', default=datetime.today()+ timedelta(days=20))
    #datetime.today() - timedelta(days=1)
    currency_id = fields.Many2one('res.currency',compute='_get_totalCotizacion')
    diasDespues = fields.Integer(string="Dias despues cierre")

    def _get_totalCotizacion(self):
        for record in self:
            cotizacion = record.env['sale.order'].search([('opportunity_id', '=',record.id )], limit=1)
            record.totalcotizacion=cotizacion.amount_total
            record.currency_id=cotizacion.currency_id
            if cotizacion.id:
                sql = "update crm_lead set totalcotizacion=%s where id=%s" % (cotizacion.amount_total,cotizacion.opportunity_id.id)
                self._cr.execute(sql)

    ###@api.multi
    def action_set_lost(self):
        """ Lost semantic: probability = 0, active = False """
        vals = super(crm_lead_v1, self).action_set_lost()
        self.write({'probability': 0, 'active': True})
        return vals

    ###@api.multi
    def contador_dias(self):
        orders = self.env["crm.lead"].search([])
        for record in orders:
            if record.date_deadline:
                tiempoDiferencia = fields.Date.from_string(fields.Date.today()) - fields.Date.from_string(record.date_deadline)
                dias= int(tiempoDiferencia.days) 
                if dias>0:
                    if record.probability<100.00:
                        vals ={'diasDespues': dias}
                        #vals ={'prueba': str(dias)}
                        record.write(vals)


'''class Myrespartner(models.Model):
    _inherit = 'res.partner'

    phone = fields.Char(string="Teléfono",required=True)'''
