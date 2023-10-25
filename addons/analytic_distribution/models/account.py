# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _

class AccountAccount(models.Model):
	_inherit = 'account.account'

	has_distribution = fields.Boolean(string="Distribuir cuenta")
	account_tag_id = fields.Many2one('account.analytic.tag', string="Distribución", domain=[('active_analytic_distribution','=',True)])

	allow_analytic_account_ids = fields.Many2many('account.analytic.account',string="Cuentas analíticas permitidas")