from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    internal_sales = fields.Boolean("Internal Sales")


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        stock_picking_id = self.env['stock.picking'].search([('origin', '=', self.name)], limit=1)
        if stock_picking_id:
            stock_picking_id.write({
                'internal_sales': self.internal_sales,
            })

        transport_rfq_obj = self.env['purchase.order'].search([('origin', '=', self.name)])
        if transport_rfq_obj:
            transport_rfq_obj.is_internal_purchase = self.internal_sales
        return res