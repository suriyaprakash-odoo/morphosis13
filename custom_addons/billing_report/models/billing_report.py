from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class BillingReport(models.TransientModel):
    _name = "so.po.billing.report"

    name = fields.Char(string="Order")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary('Total', currency_field='currency_id')
    amount_tax = fields.Monetary('Taxes', currency_field='currency_id')
    amount_untaxed = fields.Monetary('Untaxed Amount', currency_field='currency_id')
    type= fields.Selection([('Sales','Sales'),('Purchase','Purchase')])
    order_date = fields.Datetime("Order Date")
    product_ids = fields.Many2many("product.product", string="Products")
    product_name = fields.Text("Products")
    partner_id = fields.Many2one("res.partner",string="Customer/Vendor")
    company_id = fields.Many2one("res.company", string="Company")
    inv_total = fields.Monetary('Invoiced', currency_field='currency_id')
    inv_due = fields.Monetary('Amount Due', currency_field='currency_id')
    total_paid = fields.Monetary("Paid", currency_field='currency_id')
    to_invoice = fields.Monetary("To Invoice", currency_field='currency_id')
    to_invoice_untaxed = fields.Monetary("Without Tax", currency_field='currency_id')

    def generate_billing_report(self):
        lines = []
        for so in self.env['sale.order'].search([('state','=','sale')]):
            sl_line = []
            sl_product_list = []
            so_line = self.env['sale.order.line'].search([('order_id','=',so.id)])
            for sl in so_line:
                if sl.product_id:
                    sl_line.append(sl.product_id.id)
                    if sl.product_id.property_account_income_id:
                        sl_product_list.append(str(sl.product_id.name)+' ('+str(sl.product_id.property_account_income_id.code)+' '+str(sl.product_id.property_account_income_id.name)+')')
                    else:
                        sl_product_list.append(str(sl.product_id.name))
            
            inv_total = 0
            inv_due = 0
            paid = 0
            if so.invoice_ids:
                for inv in so.invoice_ids:
                    inv_total += inv.amount_total
                    inv_due += inv.amount_residual
                    paid += (inv.amount_total - inv.amount_residual)
            to_invoice = so.amount_total - inv_total
            if not round(paid) == round(so.amount_total):
                so_report = self.env['so.po.billing.report'].create({
                    'name': so.name,
                    'amount': so.amount_total,
                    'type': 'Sales',
                    'order_date': so.date_order,
                    'product_ids' : [(6, 0, sl_line)],
                    'product_name' : ', '.join(sl_product_list),
                    'amount_untaxed': so.amount_untaxed,
                    'amount_tax': so.amount_tax,
                    'partner_id' : so.partner_id.id,
                    'company_id': so.company_id.id,
                    # 'inv_total' : inv_total,
                    'inv_total' : so.amount_untaxed,
                    'inv_due' : inv_due,
                    'total_paid': paid,
                    'to_invoice': to_invoice,
                    'to_invoice_untaxed': so.amount_untaxed - paid
                })
                lines.append(so_report.id)

        for po in self.env['purchase.order'].search([('state','=','purchase')]):
            pl_line = []
            pl_product_list = []
            po_line = self.env['purchase.order.line'].search([('order_id', '=', po.id)])
            for pl in po_line:
                if pl.product_id:
                    pl_line.append(pl.product_id.id)
                    if pl.product_id.property_account_expense_id:
                        pl_product_list.append(str(pl.product_id.name)+' ('+str(pl.product_id.property_account_expense_id.code)+' '+str(pl.product_id.property_account_expense_id.name)+')')
                    else:
                        pl_product_list.append(str(pl.product_id.name))
            
            inv_total = 0
            inv_due = 0
            paid = 0
            if po.invoice_ids:
                for inv in po.invoice_ids:
                    inv_total += inv.amount_total
                    inv_due += inv.amount_residual
                    paid += (inv.amount_total - inv.amount_residual)
            to_invoice = po.amount_total - inv_total
            if not round(paid) == round(po.amount_total):
                po_report = self.env['so.po.billing.report'].create({
                    'name': po.name,
                    'amount': po.amount_total,
                    'type': 'Purchase',
                    'order_date': po.date_approve,
                    'product_ids': [(6, 0, pl_line)],
                    'product_name': ', '.join(pl_product_list),
                    'amount_untaxed': po.amount_untaxed,
                    'amount_tax': po.amount_tax,
                    'partner_id': po.partner_id.id,
                    'company_id': po.company_id.id,
                    # 'inv_total': inv_total,
                    'inv_total' : po.amount_untaxed,
                    'inv_due': inv_due,
                    'total_paid': paid,
                    'to_invoice': to_invoice,
                    'to_invoice_untaxed': po.amount_untaxed - paid
                })
                lines.append(po_report.id)

        return {
            'name': "Billing Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'res_model': 'so.po.billing.report',
            'target': 'current',
            'domain': [('id', '=', [x for x in lines])],
            'context': {
                'search_default_group_type': True,
            }
        }