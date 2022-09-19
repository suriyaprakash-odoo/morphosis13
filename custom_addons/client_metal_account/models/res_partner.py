from odoo import fields, models, api, _
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    metal_location_id = fields.Many2one("stock.location", string="Precious Metal Location")