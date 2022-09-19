from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = "stock.picking"

    internal_sales = fields.Boolean("Internal Sales")