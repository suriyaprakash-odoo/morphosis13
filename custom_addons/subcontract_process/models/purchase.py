from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sub_contract = fields.Boolean("Sub Contract Order")

    def button_confirm(self):
        result = super(PurchaseOrder, self).button_confirm()
        print (self.is_internal_purchase,self.sub_contract)
        picking_id = self.env['stock.picking'].search([('origin', '=', self.name)],limit=1)
        if picking_id:
            picking_id.is_internal_purchase = self.is_internal_purchase
            picking_id.sub_contract = self.sub_contract
        return result