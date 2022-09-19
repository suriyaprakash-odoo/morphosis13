from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_threshold = fields.Float("Billing Threshold")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    approver_id = fields.Many2one("res.users", string="Invoice/Bills Approver")