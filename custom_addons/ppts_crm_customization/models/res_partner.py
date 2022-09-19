from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_d3e = fields.Boolean("Client D3E")