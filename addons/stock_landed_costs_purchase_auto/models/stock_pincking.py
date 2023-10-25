# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class MyStockPicking(models.Model):
    _inherit = 'stock.picking'

    land_cost=fields.Many2one('stock.landed.cost', string="Costo destino")
    numero_embarque = fields.Char(string='Numero de embarque')

    '''@api.multi
    def name_get(self):
        res = []
        for record in self:
            if record.numero_embarque:
                res.append((record.id, "%s %s" % (record.name, record.numero_embarque)))
            else:
                res.append((record.id, "%s" % record.name))
        return res'''

    def crear_factura(self):
        if self.picking_type_id.name=='Recepciones':
            idcompra=self.env["purchase.order"].search([['name', '=', self.origin]]).id
            myinvoice=self.env['account.move'].sudo().create({
                        'partner_id': self.partner_id.id,
                        'currency_id': self.env.user.company_id.currency_id.id,
                        'origin': self.group_id.name,
                        'state': 'draft',
                        'type': 'in_invoice',
                        'purchase_id':int(idcompra)})
            myinvoice.purchase_order_change()
            for line in self.pack_operation_product_ids:
                sql = "update account_move_line set quantity=%s where product_id=%s and invoice_id=%s" % (line.qty_done,line.product_id.id,myinvoice.id)
                self._cr.execute(sql)
                #raise Warning(sql)

