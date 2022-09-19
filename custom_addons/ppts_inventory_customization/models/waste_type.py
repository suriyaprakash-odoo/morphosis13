from odoo import fields, models, api, _

class WasteType(models.Model):
    _name = 'waste.type'
    _description = 'Type of wastes'

    name = fields.Char("Designation",required=True)
    category = fields.Char("Category",required=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

