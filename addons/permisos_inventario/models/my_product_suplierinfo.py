#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, AccessError
import logging


class SuppliferInfo(models.Model):
    _inherit = "product.supplierinfo"

    price_anterior = fields.Float(
        'Precio ante.', default=0.0, digits=dp.get_precision('Product Price'),
        required=True, help="The price to purchase a product")

class purchase_order_v2(models.Model):
    _inherit = 'purchase.order'

    ###@api.multi
    def _add_supplier_to_product(self):
        # Add the partner in the supplier list of the product if the supplier is not registered for
        # this product. We limit to 10 the number of suppliers for a product to avoid the mess that
        # could be caused for some generic products ("Miscellaneous").
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            if partner not in line.product_id.seller_ids.mapped('name') and len(line.product_id.seller_ids) <= 10:
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                supplierinfo = {
                    'name': partner.id,
                    'sequence': max(line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
                    #'uom.uom': line.uom.uom.id,
                    'min_qty': 0.0,
                    'price_anterior': self.currency_id.compute(line.price_unit, currency),
                    'price': self.currency_id.compute(line.price_unit, currency),
                    'currency_id': currency.id,
                    'delay': 0,
                }
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    #date=line.order_id.date_order and line.order_id.date_order[:10],
                    #uom_id=line.uom.uom)
                )
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break
