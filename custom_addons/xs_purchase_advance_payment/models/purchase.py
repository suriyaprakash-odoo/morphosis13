# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    def _get_amount(self):
        advance_amount = 0.0
        for line in self.account_payment_ids:
            if line.state != 'draft':
                advance_amount += line.amount
        self.amount_resisual = self.amount_total - advance_amount

    account_payment_ids = fields.One2many('account.payment', 'purchase_id', string="Pay Purchase Advanced")
    amount_resisual = fields.Float('Residual amount', readonly=True, compute="_get_amount")
