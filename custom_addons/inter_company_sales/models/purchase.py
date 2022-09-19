from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

