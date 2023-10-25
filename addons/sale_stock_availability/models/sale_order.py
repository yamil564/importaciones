# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models, api, _, exceptions
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ##@api.one
    @api.depends(
        'product_uom_qty',
        'product_id')
    def _fnct_line_stock(self):
        available = False
        # if self.order_id.state == 'draft':
        #     available = self.product_id.with_context(
        #         warehouse=self.order_id.warehouse_id.id
        #     ).virtual_available - self.product_uom_qty
        self.virtual_available = available
        if available >= 0.0:
            available = True
        else:
            available = False
        self.virtual_available_boolean = available

    virtual_available = fields.Float(
        compute="_fnct_line_stock", string='Saldo Stock')
    virtual_available_boolean = fields.Boolean(
        compute="_fnct_line_stock", string='Saldo Stock')

    @api.onchange('product_uom_qty', 'uom.uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = super(SaleOrderLine,
                    self)._onchange_product_id_check_availability()
        if self.order_id.warehouse_id.disable_sale_stock_warning or False:
            res.update({'warning': {}})
            #res.update({'warning': warning_mess})
        return res

    @api.onchange('product_uom_qty', 'uom.uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty:
            self.product_packaging = False
            return {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        #if self.product_id.type == 'product':
        #    product_qty = self.uom.uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
        #   if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
        #        is_available = self._check_routing()
        #        if not is_available:
        #            warning_mess = {
        #                'title': _('¡No hay suficiente inventario!'),
        #               'message' : _('Usted planea vender %s %s pero solo tiene %s %s previsto disponible!\nEl stock fisico es %s %s.') % \
        #                    (self.product_uom_qty, self.uom.uom.name, self.product_id.virtual_available, self.product_id.uom_id.name, self.product_id.qty_available, self.product_id.uom_id.name)
        #           }
        #           return {'warning': warning_mess}
        #
        if self.product_id.type == 'consu':
            bom = self.env['mrp.bom'].sudo()._bom_find(product=self.product_id)
            if bom and bom.type == 'phantom':
                for line in bom.bom_line_ids:
                    if line.product_id.type == 'product':
                        product_qty = self.uom.uom._compute_quantity(line.product_qty, line.product_uom_id)
                        if float_compare(line.product_id.virtual_available, product_qty,
                                         precision_digits=precision) == -1:
                            is_available = self._check_routing()
                            if not is_available:
                                warning_mess = {
                                    'title': _('Not enough inventory for product %s!' % line.product_id.display_name),
                                    'message': _(
                                        'Usted planea vender %s %s del componente %s pero solo tiene %s %s disponible!\nEl stock fisico es %s %s.') % \
                                               (line.product_qty, line.product_uom_id.name,
                                                line.product_id.display_name,
                                                line.product_id.virtual_available, line.product_id.uom_id.name,
                                                line.product_id.qty_available, line.product_id.uom_id.name)
                                }
                                return {'warning': warning_mess}
        return {}

class sale_order_v3(models.Model):#Picking
    _inherit = 'sale.order'

    
    ##@api.multi
    def action_confirm(self):
        sum=0
        for lineas in self.order_line:
            if lineas.product_id.type == 'product':
                if str(lineas.virtual_available_boolean)=='False':
                    sum=sum+1
            if lineas.product_id.type == 'consu':
                bom = self.env['mrp.bom'].sudo()._bom_find(product=lineas.product_id)
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if bom and bom.type == 'phantom':
                    for line in bom.bom_line_ids:
                        if line.product_id.type == 'product':
                            product_qty = lineas.uom.uom._compute_quantity(line.product_qty, line.product_uom_id)
                            if float_compare(line.product_id.virtual_available, product_qty,
                                            precision_digits=precision) == -1:
                                is_available = lineas._check_routing()
                                if not is_available:
                                    sum=sum+1
        if sum>0:
            raise exceptions.ValidationError(
            _('Usted no tiene stock suficiente en sus productos sombreados.'))
        else:
            res = super(sale_order_v3, self).action_confirm()
            #res = self.env['report.seguimiento.pedidos']._compute_pedidos()
        return res