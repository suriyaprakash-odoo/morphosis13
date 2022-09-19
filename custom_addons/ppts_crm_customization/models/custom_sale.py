from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.price_total', 'amount_from_offer')
    def _amount_all(self):
        for order in self:
            if not order.opportunity_id:
                amount_untaxed = amount_tax = 0.0
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                order.update({
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': amount_untaxed + amount_tax,
                })
            else:
                amount_untaxed = amount_tax = 0.0
                amount_total = 0.0
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                if order.opportunity_id.total_offer_price_transport:
                    amount_total = order.opportunity_id.total_offer_price_transport + amount_tax
                else:
                    amount_total = amount_untaxed + amount_tax
                order.update({
                    'amount_untaxed': amount_untaxed,
                    'amount_tax': amount_tax,
                    'amount_total': amount_total,
                })

    amount_from_offer = fields.Monetary(string='Offered Amount', store=True, readonly=True, tracking=True)
