from odoo import models, api, fields
from odoo.addons.gestionit_pe_fe.models.number_to_letter import to_word
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_view_invoice(self):
        res = super(PurchaseOrder, self).action_view_invoice()
        res["context"].update({"default_invoice_type_code": "01", 
                                "default_journal_type": "purchase"})
        # _logger.info(res)
        return res

    def to_word(self, monto, moneda):
        return to_word(monto, moneda)

    @staticmethod
    def custom_date_format(date_str):
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            month_names = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
            formatted_date = date_obj.strftime('Lima, %d de {} de %Y'.format(month_names[date_obj.month - 1]))
            return formatted_date
        else:
            return ''

