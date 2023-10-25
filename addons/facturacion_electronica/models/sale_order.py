# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp

class PaymentTerms(models.Model):
    _name = "termino.pago.sunat"
    nombre = fields.Char("Nombre",compute="_compute_name")
    invoice_date_due = fields.Date("Fecha de Vencimiento")
    amount = fields.Float("Monto")
    number_id = fields.Integer("Id")
    sale_ord = fields.Many2one('sale.order',string="Pedido",readonly="1")
    account_inv = fields.Many2one('account.move',string="Factura",readonly="1")
    #@api.one
    def _compute_name(self):
        self.nombre='Cuota-'+str(self.id)
    
    ##@api.one
    #def _compute_id(self):
        #self.number_id=self.account_inv.id

class accountpaymentterm_v2(models.Model):
    _inherit = "account.payment.term"
    forma_de_pago = fields.Selection(
        string="Forma de Pago",
        selection=[
            ("Contado", "Contado"),
            ("Credito", "Credito")
        ],
        default="Contado",
    )

class saleOrder(models.Model):
    _inherit = "sale.order"
    
    _order = "name desc"
    
    tipo_documento = fields.Selection(string="Tipo de Documento",selection=[('01','Factura'),('03','Boleta')], required=True, default='01')
    termino_pago_sunat = fields.One2many('termino.pago.sunat','sale_ord', string='Datos de termino de Pago')  #, domain=[('active', '=', True)] force "active_test" domain to bypass _search() override
    forma_de_pago = fields.Selection(
        string="Forma de Pago",
        selection=[
            ("Contado", "Contado"),
            ("Credito", "Credito")
        ],
        default="Contado",
    )

    ##@api.multi
    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            # action['domain'] = [('journal_id.invoice_type_code_id','=','01')]
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]

            #default_journal_id = self.env["account.journal"].search([["invoice_type_code_id", "=", self.tipo_documento]])
            #action["context"] = "{'type_code':'"+self.tipo_documento+"'}"
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    ##@api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}
        default_journal_id = self.env["account.journal"].search([["invoice_type_code_id", "=", '01']])
        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.client_order_ref and order.client_order_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key]),
                                       'journal_id':str(default_journal_id.id)
                                       })#'journal_id':str(default_journal_id.id)

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        
        for i in invoices.values():
            i.final = True
        return [inv.id for inv in invoices.values()]