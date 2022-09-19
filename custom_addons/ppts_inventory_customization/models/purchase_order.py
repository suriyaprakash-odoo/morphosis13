from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare


class ProductProduct(models.Model):
    _inherit = "product.product"

    account_rel = fields.Char('Ref',invisible=True,store=True, compute="_compute_account")
    income_account = fields.Many2one('account.account', 'Income Account', readonly=True)
    expense_account = fields.Many2one('account.account', 'Expense Account', readonly=True)

    @api.depends('property_account_income_id')
    def _compute_account(self):
        for loop in self:
            if loop.property_account_income_id:
                loop.income_account = loop.property_account_income_id.id
                loop.expense_account = loop.property_account_income_id.id

class SaleReport(models.Model):
    _inherit = 'sale.report'

    income_account = fields.Many2one('account.account', 'Income Account', readonly=True)
    expense_account = fields.Many2one('account.account', 'Expense Account', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['income_account'] = ", p.income_account as income_account"
        fields['expense_account'] = ', p.expense_account as expense_account'

        groupby += ',p.income_account, p.expense_account'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    income_account = fields.Many2one('account.account', 'Income Account', readonly=True)
    expense_account = fields.Many2one('account.account', 'Expense Account', readonly=True)

    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

    def _select(self):
        return super(PurchaseReport, self)._select() + ", p.income_account as income_account, p.expense_account as expense_account, po.invoice_status as invoice_status"

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", spt.warehouse_id, p.income_account, p.expense_account, po.invoice_status"

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    next_revision_number = fields.Char('Next Revision Number', default='01')
    purchase_revision_ids = fields.One2many('purchase.revision.history', 'purchase_revision_id', string = 'Revision Line ref')

    def button_confirm(self):
        result = super(PurchaseOrder, self).button_confirm()
        picking_id = self.env['stock.picking'].search([('origin', '=', self.name)],limit=1)
        if picking_id:
            move_line = self.env["stock.move"].search([('picking_id', '=', picking_id.id)])
            for line in move_line:
                if self.partner_id.country_id.code=='FR':
                    line.write({'bsd_annexe': 'bsd'})
                else:
                    line.write({'bsd_annexe': 'annexe7'})
        return result

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _create_or_update_picking(self):
        for line in self:
            if line.product_id.type in ('product', 'consu'):
                # Prevent decreasing below received quantity
                # if float_compare(line.product_qty, line.qty_received, line.product_uom.rounding) < 0:
                #     raise UserError(_('You cannot decrease the ordered quantity below the received quantity.\n'
                #                       'Create a return first.'))

                if float_compare(line.product_qty, line.qty_invoiced, line.product_uom.rounding) == -1:
                    # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                    # inviting the user to create a refund.
                    activity = self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                        'note': _('The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
                        'res_id': line.invoice_lines[0].invoice_id.id,
                        'res_model_id': self.env.ref('account.model_account_move').id,
                    })
                    activity._onchange_activity_type_id()

                # If the user increased quantity of existing line or created a new line
                pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit'))
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.order_id._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                move_vals = line._prepare_stock_moves(picking)
                for move_val in move_vals:
                    self.env['stock.move']\
                        .create(move_val)\
                        ._action_confirm()\
                        ._action_assign()

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        for line in self:
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                for move in line.move_ids:
                    if move.state == 'done':
                        if move.location_dest_id.usage == "supplier":
                            if move.to_refund:
                                total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                if line.order_id.is_sorted == True:
                	line.qty_received = line.product_qty
                else:
                	line.qty_received = total


class PurchaseRevisionHistory(models.Model):
	_name = 'purchase.revision.history'

	po_number = fields.Char('Name')
	partner_id = fields.Many2one('res.partner', string='Vendor')
	purchase_revision_id = fields.Many2one('purchase.order', string='Revision line ref')

	revision_product_line_ids = fields.One2many('revision.line', 'revision_product_line_id', string='Product Line ref')


class RevisionHistoryLine(models.Model):
	_name = 'revision.line'

	product_id = fields.Many2one('product.product', string = 'Product')
	description = fields.Char('Description')
	product_qty = fields.Float('Quantity')
	product_uom = fields.Many2one('uom.uom', string = 'Uom')
	price_unit = fields.Float('Unit Price')
	currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
	price_subtotal = fields.Monetary('Price Subtotal', currency_field='currency_id')

	revision_product_line_id = fields.Many2one('purchase.revision.history', string = 'Product Line Ref')