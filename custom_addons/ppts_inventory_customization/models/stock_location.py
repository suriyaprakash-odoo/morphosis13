# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class Location(models.Model):
    _inherit = "stock.location"
    _description = "Inventory Locations"

    is_vrac_location = fields.Boolean('Is Vrac Location')
    is_stock_location = fields.Boolean("Is a Stock location?")
    chronopost_location = fields.Boolean("Is Chronopost Location?")