#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging
#

class product_product_v4(models.Model):
    _inherit = 'product.template'

    codigo_purchase = fields.Char(string='Codigo Proveedor')
