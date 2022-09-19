from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    name = fields.Char('Lot/Serial Number', default=lambda self: self.env['ir.sequence'].next_by_code('stock.lot.serial.new'),
        required=True, help="Unique Lot/Serial Number")
    purity = fields.Float("Purity", digits=(3, 1))

    _sql_constraints = [
        ('name_ref_uniq', 'unique (name, product_id, company_id)', 'The combination of serial number and product must be unique across a company !'),
    ]
