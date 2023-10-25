#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    
    bl = fields.Char(string='BL')
    picking_ids = fields.Many2many(
        'stock.picking', string='Pickings',
        copy=True, states={'done': [('readonly', True)]})
    purchase_ids = fields.Many2many("purchase.order", string='Ordenes',compute="_compute_ordenes")
    names_purchase_ids = fields.Char(string='Ordenes de Compra')#related='purchase_ids.name', store=True,
    M2M_purchase_ids = fields.Char(string='Ordenes de Compra')
    stock_valuario_orderlines = fields.One2many(
        'stock.valuation.orderline', 'cost_id', string='Prorrateo')
    amount_subtotal_prorrateo = fields.Float(
        'SubTotal', compute='_compute_total_amount_prorrateo', store=True)
    amount_total_prorrateo = fields.Float(
        'Total', compute='_compute_total_amount_prorrateo', store=True)
    account_journal_id = fields.Many2one('account.journal', 'Diario Contable',required=True, states={'done': [('readonly', True)]},
        help=' El Libro Diario, también conocido como Libro de Cuentas,\n'
                'es un documento contable obligatorio que recoge el día a\n'
                'día de los hechos económicos de la empresa. Es decir, es\n'
                'aquel donde se anotan los gastos, deudas y ganancias diarias.\n',
                default=lambda self: self.env['account.journal'].search([], limit=1))
    currency_id = fields.Many2one('res.currency', string='Moneda',default=lambda self: self.env.user.company_id.currency_id)
    
    
    def button_validate(self):
        res=super(StockLandedCost, self).button_validate()
        vals = {'land_cost':self.id}
        for record in self.picking_ids:
            self.env['stock.picking'].search([('id','=',record.id)]).write(vals)
        return True

    
    def button_cancel(self):
        if any(cost.state == 'done' for cost in self):
            self.copy()
        return self.write({'state': 'cancel'})

    
    @api.depends('stock_valuario_orderlines.final_cost')
    def _compute_total_amount_prorrateo(self):
        for record in self:
            record.amount_subtotal_prorrateo = sum(line.final_cost for line in record.stock_valuario_orderlines)
            record.amount_total_prorrateo = record.amount_subtotal_prorrateo*1.18

    def _compute_ordenes(self):
        for record in self:
            lista2=' '
            coma=' '
            for movimiento in record.picking_ids:  
                idcompra=self.env["purchase.order"].search([['name', '=', movimiento.group_id.name]]).id
                lista=movimiento.group_id.name
                lista2=lista+coma+lista2
                coma=' , ' 
                record.purchase_ids=[(4,idcompra)]
                
            record.write({'names_purchase_ids': str(lista2)})

    def get_valuation_lines(self):
        lines = []

        for pick in self.mapped('picking_ids'):
            for move in pick.mapped('move_lines'):
                # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
                if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel' or not move.product_qty:
                    continue
                vals = {
                    'name_order':str(pick.group_id.name),
                    'product_id': move.product_id.id,
                    'move_id': move.id,
                    'quantity': move.product_qty,
                    'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),#sum(quant.cost * quant.qty for quant in move.quant_ids),
                    'weight': move.product_id.weight * move.product_qty,
                    'volume': move.product_id.volume * move.product_qty
                }
                lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
        return lines

    
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        digits = self.env['decimal.precision'].precision_get('Product Price')
        #digits = dp.get_precision('Product Price')(self._cr)
        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost.picking_ids):
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            former_cost2 = 0.0
            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id,'suma_costes':cost.amount_total})#,'name_order':str(cost.picking_ids.group_id.name)
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                self.env['stock.valuation.orderline'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)
                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                #total_cost += tools.float_round(former_cost, precision_digits=digits[1]) if digits else former_cost
                total_cost += tools.float_round(former_cost, precision_digits=digits) if digits else former_cost

                total_line += 1
            former_cost2=0
            for pick in cost.mapped('picking_ids'):
                for move in pick.mapped('move_lines'):
                    #former_cost2 = sum(move.stock_valuation_layer_ids.mapped('value')),#sum(quant.cost * quant.qty for quant in move.quant_ids)
                    former_cost2 = sum(move.stock_valuation_layer_ids.mapped('unit_cost'))*move.quantity_done + former_cost2,
                    former_cost2 = float(former_cost2[0])
            #raise Warning(_(former_cost2))
            self.env['stock.valuation.orderline'].search([('cost_id', 'in', self.ids)]).write({'sum_former_cost': former_cost2})
            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if digits:#tools.float_round(value, precision_digits=digits[1]
                            value = tools.float_round(value, precision_digits=digits, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        if towrite_dict:
            for key, value in towrite_dict.items():
                AdjustementLines.browse(key).write({'additional_landed_cost': value})
        return True


class MyAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    order_id = fields.Many2one('purchase.order', 'Orden', readonly=True)
    suma_costes = fields.Float(
        'Suma Costo Adicional',
        digits=dp.get_precision('Product Price'))
    name_order = fields.Char('Orden')


class stockValuationOrderline(models.Model):
    _name = 'stock.valuation.orderline'
    _description = 'Stock Valuation para Order Lines'

    name = fields.Char(
        'Descripcion', compute='_compute_name', store=True)
    cost_id = fields.Many2one(
        'stock.landed.cost', 'Embarque')#,required=True ondelete='cascade',
    cost_line_id = fields.Many2one('stock.landed.cost.lines', 'Cost Line', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Moneda',related='cost_id.currency_id')
    order_line_id = fields.Many2one('purchase.order.line', 'Lineas de Orden', readonly=True)
    order_id = fields.Many2one('purchase.order', 'Orden', readonly=True)
    name_order = fields.Char('Orden')
    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True)
    product_id = fields.Many2one('product.product', 'Productos')#, required=True
    quantity = fields.Float(
        'Cantidad', default=1.0,
        digits=0)#, required=True
    weight = fields.Float(
        'Ancho', default=1.0,
        digits=dp.get_precision('Stock Weight'))
    volume = fields.Float(
        'Volumen', default=1.0)
    former_cost = fields.Float(
        'SubTotal FOB', digits=dp.get_precision('Product Price'))
    sum_former_cost = fields.Float(
        'Suma SubTotal FOB', digits=dp.get_precision('Product Price'))
    former_cost_per_unit = fields.Float(
        'Precio FOB', compute='_compute_former_cost_per_unit',
        digits=0, store=True)
    additional_landed_cost = fields.Float(
        'Costo Adicional', compute='_compute_additional_landed_cost', store=True)
    final_cost = fields.Float(
        'Total', compute='_compute_final_cost', store=True)
    final_precio = fields.Float(
        'Precio Final', compute='_compute_final_cost', store=True)
    suma_costes = fields.Float(
        'Suma Costo Adicional',
        digits=dp.get_precision('Product Price'))

    @api.depends( 'product_id.code', 'product_id.name')
    def _compute_name(self):
        for record in self:
            record.name = str(record.id) + (record.product_id.code or record.product_id.name or '')

    @api.depends('former_cost', 'quantity')
    def _compute_former_cost_per_unit(self):
        for record in self:
            record.former_cost_per_unit = record.former_cost / (record.quantity or 1.0)

    @api.depends('sum_former_cost','suma_costes')
    def _compute_additional_landed_cost(self):
        for record in self:
            record.additional_landed_cost = round( (record.sum_former_cost+record.suma_costes)/(record.sum_former_cost or 1.0) ,4)

    @api.depends('former_cost', 'additional_landed_cost')
    def _compute_final_cost(self):
        for record in self:
            record.final_precio = record.former_cost_per_unit * record.additional_landed_cost
            record.final_cost = record.former_cost_per_unit * record.additional_landed_cost * record.quantity

    @api.depends('former_cost', 'additional_landed_cost')
    def _actualizar_precio_supplierinfo(self):
        for record in self:
            final_precio = record.former_cost_per_unit * record.additional_landed_cost
            sql = "update product_supplierinfo set price=%s where product_id=%s" % (final_precio,record.product_id.id)
            self._cr.execute(sql)
            #raise Warning(_(sql))