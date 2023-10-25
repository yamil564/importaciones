from odoo import models, api, exceptions

class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.split_method = 'by_current_cost_price' 
        


 
