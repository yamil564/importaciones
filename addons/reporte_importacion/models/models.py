from odoo import models, fields

class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    way_of_shipment = fields.Char(string="Way of Shipment")
