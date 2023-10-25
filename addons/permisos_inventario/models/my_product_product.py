#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging

class product_product_v5(models.Model):
    _inherit = 'product.template'

    costo_promedio = fields.Float(string="Costo promedio")
    cantidadprueba = fields.Float(string="Cantidad")
    promedioprueba = fields.Float(string="Promedio:")
    
    
