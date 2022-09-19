from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    internal_company = fields.Boolean("Internal Company")