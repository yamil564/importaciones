#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


class res_users_v2(models.Model):
    _inherit = 'res.users'

    sede = fields.Many2one('users.sede', string='Sede')

class res_users_sede(models.Model):
    _name = 'users.sede' 

    name = fields.Char(string="Nombre") 
    almacen = fields.Many2one('stock.warehouse', string='Almacen')