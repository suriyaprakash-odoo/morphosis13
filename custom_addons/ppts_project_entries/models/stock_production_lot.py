from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning

class StockproductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def default_get(self, fields_name):
        res = super(StockproductionLot, self).default_get(fields_name)


        print(self.env.context)

        return res