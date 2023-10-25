# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        if self.product_id.type == 'product':
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id)
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()
                if not is_available:
                    message =  _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
                            (self.product_uom_qty, self.product_uom.name, product.virtual_available, product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available accross all warehouses.') % \
                                (self.product_id.virtual_available, product.uom_id.name)

                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message' : message
                    }
                    return {'warning': warning_mess}
        if self.product_id.type == 'consu':
            bom = self.env['mrp.bom'].sudo()._bom_find(product=self.product_id)
            if bom and bom.type == 'phantom':
                for line in bom.bom_line_ids:
                    if line.product_id.type == 'product':
                        product_qty = self.product_uom._compute_quantity(line.product_qty, line.product_uom_id)
                        if float_compare(line.product_id.virtual_available, product_qty,
                                         precision_digits=precision) == -1:
                            is_available = self._check_routing()
                            if not is_available:
                                warning_mess = {
                                    'title': _('Not enough inventory for product %s!' % line.product_id.display_name),
                                    'message': _(
                                        'You plan to sell %s %s but you only have %s %s available!\nThe stock on hand is %s %s.') % \
                                               (line.product_qty, line.product_uom_id.name,
                                                line.product_id.virtual_available, line.product_id.uom_id.name,
                                                line.product_id.qty_available, line.product_id.uom_id.name)
                                }
                                return {'warning': warning_mess}
        return {}