# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression

class AccountAnalyticDistribution(models.Model):
	_inherit = 'account.analytic.distribution'

	account_destino_id = fields.Many2one('account.account', string="Cuenta de distribucion", required=False)
	account_contra_id = fields.Many2one('account.account', string="Cuenta contrapartida")

	@api.onchange('account_id')
	def onchange_account_destino_contra_id(self):
		for rec in self:
			if rec.account_id:
				rec.account_destino_id = rec.account_id.account_destino_id 
				rec.account_contra_id = rec.account_id.account_contra_id


class AccountAnalyticTag(models.Model):
	_inherit = 'account.analytic.tag'

	is_account_contra_unique = fields.Boolean(string="Usar Cuenta contrapartida única",default=False)

	account_contra_id = fields.Many2one('account.account',string="Cuenta contrapartida única")


class AccountAnalyticAccount(models.Model):
	_inherit = 'account.analytic.account'

	account_destino_id = fields.Many2one('account.account', string="Cuenta de distribucion", required=False)
	account_contra_id = fields.Many2one('account.account', string="Cuenta contrapartida")


	def name_get(self):
		res = []
		for analytic in self:

			name = analytic.name
			if analytic.code:
				name = '[' + analytic.code + '] ' + name

			if analytic.account_destino_id and analytic.account_destino_id.code:
				name =  name + ' [' + analytic.account_destino_id.code + '] '

			if analytic.partner_id.commercial_partner_id.name:
				name = name + ' - ' + analytic.partner_id.commercial_partner_id.name
			res.append((analytic.id, name))
		return res


	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
			return super(AccountAnalyticAccount, self)._name_search(name, args, operator, limit, name_get_uid=name_get_uid)
		args = args or []
		if operator == 'ilike' and not (name or '').strip():
			domain = []
		else:
			partner_ids = self.env['res.partner']._search([('name', operator, name)], limit=limit, access_rights_uid=name_get_uid)
			domain = ['|', '|', '|',('code', operator, name),('account_destino_id.code',operator,name) ,('name', operator, name), ('partner_id', 'in', partner_ids)]
		analytic_account_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
		return models.lazy_name_get(self.browse(analytic_account_ids).with_user(name_get_uid))