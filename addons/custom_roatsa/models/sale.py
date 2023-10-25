#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
import logging


_logger = logging.getLogger(__name__)


class gastosAdicionales(models.Model):
    _name = "sale.adicional.line"

    descripcion = fields.Char(string="Descripcion")
    monto = fields.Float(string="Monto", default=0.0,
                         digits=dp.get_precision('Account'))
    order_id = fields.Many2one('sale.order', string="Orden de ventas")


class ordenVentaLine(models.Model):
    _inherit = "sale.order.line"

    ###@api.multi
    def _compute_order_number(self):
        for rec in self:
            rec.order_number = rec.order_id.name

    codigo_proveedor = fields.Char(string="Cod. proveedor")
    cod_prov = fields.Boolean(related='order_id.cod_prov')
    disponibilidad = fields.Char(string="Disponibilidad", default="Inmediata")
    order_number = fields.Char(string="Orden", compute='_compute_order_number')
    kit_id = fields.Many2one("sale.kit.line", string="Kit")
    price_prueba=fields.Char(string="price")

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','price_prueba')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price=round(price,2)
            line.price_prueba=price
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

class ordenVentaKit(models.Model):
    _name = "sale.kit.line"

    ###@api.multi
    def _compute_monto(self):
        for rec in self:
            monto = 0
            lines = self.env['sale.order.line'].search(
                [["kit_id", "in", [rec.id]]])
            for line in lines:
                monto += line.price_subtotal

            rec.monto = monto

    name = fields.Char(string="Descripción")
    detalle = fields.Text(string="Detalle del contenido")
    monto = fields.Float(string="Monto", default=0.0, compute='_compute_monto')
    order_id = fields.Many2one("sale.order", string="Cotización/Pedido")
    line_ids = fields.One2many(
        "sale.order.line", "kit_id", string="Línea de detalle")


class ordenVenta(models.Model):
    _inherit = 'sale.order'
    # Verifica si el usuario tiene ID 2, 30, 36, 40 o 46 y no aplica el filtro en esos casos
    excluded_user_ids = [2, 30, 36, 40, 46]
    #que solo liste mis cotizaciones por seguridad
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # Verifica si el usuario tiene ID 2, 30, 36, 40 o 46 y no aplica el filtro en esos casos
        excluded_user_ids = [2, 30, 36, 40, 46]
        if self.env.user and self.env.user.id not in excluded_user_ids:
            args += [('user_id', '=', self.env.user.id)]
        return super(ordenVenta, self).search(args, offset, limit, order, count)
    
    
    detalle_gastos = fields.One2many(
        "sale.adicional.line", "order_id", string="Gastos adicionales")
    total_gastos = fields.Monetary(string="Gastos adicionales", store=True, default=0.0, digits=dp.get_precision(
        'Account'), compute="_compute_total_gastos")
    validez = fields.Char(string="Validez de la oferta", default="20 días")
    cod_prov = fields.Boolean(string="Código de proveedor?")
    nreq = fields.Char(string="# de requerimiento")
    kits = fields.One2many("sale.kit.line", "order_id", string="Kits")
    #price_prueba=fields.Char(string="price")
    #https://github.com/odoo/odoo/blob/9.0/addons/account/models/account.py#L643
    #@ #api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'custom_roatsa.pdf_cotizacion_template')

    @ api.onchange('currency_id')
    def _currency_change(self):
        if self.currency_id.name == 'USD':
            for line in self.order_line:
                line.price_unit = line.product_id.lst_price
        else:
            for line in self.order_line:
                line.price_unit = line.product_id.lst_price * self.currency_id.rate

    #@ api.one
    @ api.depends('detalle_gastos.monto')
    def _compute_total_gastos(self):
        self.total_gastos = sum([line.monto for line in self.detalle_gastos])
        self.amount_total += sum([line.monto for line in self.detalle_gastos])

    @ api.depends('order_line.price_total', 'detalle_gastos.monto')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = round(line.price_unit * \
                        (1 - (line.discount or 0.0) / 100.0) ,2)
                    #line.price_prueba=price
                    taxes = line.tax_id.compute_all(
                        price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0)
                                      for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            # order.update({
            #     'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
            #     'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
            #     'amount_total': amount_untaxed + amount_tax + order.total_gastos,
            # })

class productTemplate(models.Model):
    _inherit = "product.product"

    #@ #api.multi
    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get(
                'default_code', False) or False
            if code:
                name = '%s [%s]' % (name, code)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(
                partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id',
                          'product_template_attribute_value_ids', 'attribute_line_ids'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(
                ['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(
                    r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(
                lambda l: len(l.value_ids) > 1).mapped('attribute_id')
            # variant = product.product_template_attribute_value_ids._variant_name(
            #     variable_attributes)
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (
                product.name, variant) or product.name
            sellers = []
            if partner_ids:
                product_supplier_info = supplier_info_by_template.get(
                    product.product_tmpl_id, [])
                sellers = [
                    x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [
                        x for x in product_supplier_info if not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (
                            s.product_name, variant) or s.product_name
                    ) or False
                    mydict = {
                        'id': product.id,
                        'name': seller_variant or name,
                        'default_code': s.product_code or product.default_code,
                    }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                    'id': product.id,
                    'name': name,
                    'default_code': product.default_code,
                }
                result.append(_name_get(mydict))
        return result
