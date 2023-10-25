# -*- coding : utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PurchaseOrderUpdate(models.Model):
	_inherit = 'purchase.order'

	invoiced_amount = fields.Float(String = 'Importe facturado')
	invoiced_borrador = fields.Float(String = 'Importe borrador')
	amount_due = fields.Float(String ='Importe pendiente')
	paid_amount = fields.Float(String ='Monto pagado')
	amount_paid_percent = fields.Float()
	currency_id = fields.Many2one('res.currency', string='Moneda',default=lambda self: self.env.user.company_id.currency_id)
	
	#@api.multi
	#def _computetotal(self):
	#	invoice_id = self.env['account.move'].search(['&',('invoice_origin','=', self.name),'|',('state','=','open'),('state','=','paid')])
	#	total = 0
	#	for comp in invoice_id:
	#		total += comp.amount_total
	#	self.invoiced_amount = total

	#@api.multi
	#def _computeborrador(self):
	#	invoice_id = self.env['account.move'].search(['&',('invoice_origin','=', self.name),('state','=','draft')])
	#	total = 0
	#	for comp in invoice_id:
	#		total += comp.amount_total
	#	self.invoiced_borrador = total

	#@api.multi			
	#def _computedue(self):
	#	item_id = self.env['account.move'].search(['&',('invoice_origin','=', self.name),'|',('state','=','open'),('state','=','paid')])
	#	aggregate = 0
	#	for comp in item_id:
	#		aggregate +=comp.residual   

	#	self.amount_due = aggregate
		

	@api.onchange('invoiced_amount','amount_due')
	def _computepaid(self):
		self.paid_amount = float(self.invoiced_amount) - float(self.amount_due)		


	#@api.multi
	def action_amount_paid(self):
		if self.invoiced_amount > 0:
			self.amount_paid_percent = round(100 * self.paid_amount / self.invoiced_amount, 3)
