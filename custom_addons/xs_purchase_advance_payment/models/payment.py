# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountPayment(models.Model):

    _inherit = "account.payment"

    purchase_id = fields.Many2one('purchase.order', "Purchase", readonly=True, states={'draft': [('readonly', False)]})
