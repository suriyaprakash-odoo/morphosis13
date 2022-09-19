from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = 'res.company'

    precious_location_id = fields.Many2one("stock.location", string="Precious Metal Stock Location")