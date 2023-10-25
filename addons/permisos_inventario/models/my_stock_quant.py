#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


class stock_quant_v2(models.Model):
    _inherit = 'stock.quant'