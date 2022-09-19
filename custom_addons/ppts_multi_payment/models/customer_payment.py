from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CustomerMultiPayment(models.Model):
    _name = "customer.multi.payment"
    _order = 'name desc'
    _inherit = ['mail.thread']
    
    name = fields.Char("Name", default="Draft Receipt", tracking=True)
    partner_id = fields.Many2one('res.partner', string="Partner", domain=[('customer_rank', '>', 0)], required=True, tracking=True)
    paid_amount = fields.Float("Paid Amount", default=0.00, tracking=True)
    credit_amount = fields.Float("Credit Amount", compute='_compute_amount')
    journal_id = fields.Many2one("account.journal", string="Payment Journal", domain=[('type', 'in', ('bank', 'cash'))], tracking=True)
    payment_date = fields.Date("Payment Date", default=lambda self: fields.Date.today(), tracking=True)
    communication = fields.Char("Memo", tracking=True)
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id, readonly=True)
    payment_id = fields.Many2one('account.payment', string="Payment")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.user.company_id.currency_id, tracking=True)
    credit_line_ids = fields.One2many('customer.multi.payment.credit.line', 'multi_pay_id', string="Credit Line")
    debit_line_ids = fields.One2many('customer.multi.payment.debit.line', 'multi_pay_id', string="Debit Line")
    state = fields.Selection([('draft', "Draft"), ('posted', "Posted"), ('cancel', "Cancel")], default="draft", tracking=True)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', "Transfer")], string='Payment Type')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', required=True, oldname="payment_method",
                                        help="Manual: Get paid by cash, check or any other method outside of Odoo.\n" \
                                             "Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n" \
                                             "Check: Pay bill by check and print it from Odoo.\n" \
                                             "Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit,module account_batch_deposit must be installed.\n" \
                                             "SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    note = fields.Text("Internal Notes")
    account_move_id = fields.Many2one("account.move", string="Journal Entry", copy=False, tracking=True)
    account_move = fields.Char("Journal Entry")
    payment_difference = fields.Monetary(string="Payment Difference", store=True, compute='_compute_amount', readonly=True, tracking=True)
    currency_rate = fields.Float('Currency Rate', tracking=True)
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", domain=[('deprecated', '=', False)], copy=False)
    writeoff_label = fields.Char(string='Journal Item Label', help='Change label of the counterpart that will hold the payment difference', default='Write-Off')
    writeoff_move_id = fields.Many2one("account.move", string="Journal Entry", copy=False, tracking=True)
    
    @api.model
    def create(self, vals):
        journal_id = self.env['account.journal'].browse(vals.get('journal_id'))
        vals['name'] = journal_id.sequence_id.next_by_id()
        return super(CustomerMultiPayment, self).create(vals) 
    
    @api.depends('paid_amount','debit_line_ids.amount_to_pay','credit_line_ids.amount_to_pay')
    def _compute_amount(self):
        for val in self:
            credit = debit = 0.00
            credit = sum(line.amount_to_pay for line in self.credit_line_ids)
            debit = sum(line.amount_to_pay for line in self.debit_line_ids)
            val.credit_amount = credit - debit
            val.payment_difference = val.credit_amount - val.paid_amount
        
    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            if self.journal_id.inbound_payment_method_ids:
                self.payment_method_id = self.journal_id.inbound_payment_method_ids[0].id
            if self.journal_id.currency_id.id:
                self.currency_id = self.journal_id.currency_id.id
            else:
                self.currency_id = self.env.user.company_id.currency_id.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            invoice_ids = self.env['account.move'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'posted')])
            total_amount = 0.0
            if not invoice_ids:
                self.credit_line_ids = False
                self.debit_line_ids = False
            credit_lines = []
            debit_lines = []
            for inv in invoice_ids:
                if inv.type == 'out_invoice':
                    total_amount += inv.amount_residual
                line_vals = {
                    'description': inv.name or False,
                    'amount_invoice': inv.amount_total or False,
                    'amount_residual': inv.amount_residual or False,
                    'move_id': inv.id,
                    'invoice_date': inv.invoice_date or '',
                    'currency_id': inv.currency_id.id,
                }
                if inv.type == 'out_refund':
                    debit_lines.append((0, 0, line_vals))
                elif inv.type == 'out_invoice':
                    credit_lines.append((0, 0, line_vals))
            payment_ids = self.env['account.payment'].search([('partner_id','=',self.partner_id.id),('state','=','posted'),('partner_type','=','customer')])
            for pay in payment_ids:
                if not pay.cus_multi_pay_id:
                    move_line_id = self.env['account.move.line'].search([('payment_id','=',pay.id),('reconciled','=',False),('credit', '>', 0)])
                    if not pay.name in credit_lines and move_line_id:
                        line_vals_pay = {
                        'description': pay.name or False,
                        'amount_invoice': pay.amount or False,
                        'amount_residual': abs(move_line_id.amount_residual) or False,
                        'payment_id': pay.id,
                        'invoice_date': pay.payment_date or '',
                        'currency_id': pay.currency_id.id,
                        }
                        debit_lines.append((0, 0, line_vals_pay))
            self.debit_line_ids = debit_lines
            self.credit_line_ids = credit_lines
            self.paid_amount = total_amount

    def get_all_payment_vals(self):
        lines = []
        for line in self.debit_line_ids:
            if line.amount_reconcile != 0.0:
                lines.append(line.move_id)
        return {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'invoice_ids': [(6, 0, [x.id for x in lines])],
            'payment_type': self.payment_type,
            'amount': self.paid_amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': self.partner_type,
#             'currency_rate': self.credit_line_ids[0].currency_rate,
#             'note': self.note,
        }
 
    def cancel_payment(self):
        for line in self.debit_line_ids:
            if line.payment_id:
                move_line_ids = self.env['account.move.line'].search([('payment_id','=',line.payment_id.id)])
                move_line_ids.remove_move_reconcile()
                line.payment_id.invoice_ids = False
            if line.move_id:
                move_line_ids = self.env['account.move.line'].search([('move_id','=',line.move_id.id)])
                move_line_ids.remove_move_reconcile()
        payment_id = self.env["account.payment"].search([('cus_multi_pay_id', '=', self.id)])
        for payment in payment_id:
            for move in payment.move_line_ids.mapped('move_id'):
                if payment.invoice_ids:
                    move.line_ids.remove_move_reconcile()
                move.button_cancel()
            payment.state = 'cancelled'
            payment.cus_multi_pay_id = False
            payment.invoice_ids = False
        if self.writeoff_move_id:
            self.writeoff_move_id.line_ids.remove_move_reconcile()
            self.writeoff_move_id.button_cancel()
        self.state = 'cancel'
        
    def reset_to_draft(self):
        for line in self.credit_line_ids:
            line.amount_reconcile = line.amount_to_pay
        for line in self.debit_line_ids:
            line.amount_reconcile = line.amount_to_pay
        self.state = 'draft'
 
    def create_payments(self):
        for line in self.credit_line_ids:
            if self.currency_id.id != line.currency_id.id:
                raise UserError(_("Please select same currency"))
        for line in self.debit_line_ids:
            if self.currency_id.id != line.currency_id.id:
                raise UserError(_("Please select same currency"))
            
        if self.paid_amount > round(sum(line.amount_invoice for line in self.credit_line_ids), 4):
            raise UserError(_("Payment amount exceeds Invoice Amount"))
 
        if self.paid_amount == 0.0 and round(sum(line.amount_to_pay for line in self.credit_line_ids), 4) == 0.0:
            raise UserError(_("Please add some amount to process the invoices"))
        
        credit = sum(line.amount_to_pay for line in self.credit_line_ids)
        debit = sum(line.amount_to_pay for line in self.debit_line_ids)
        diff = self.credit_amount - self.paid_amount
        
#         for line in self.credit_line_ids:
#             if not line.amount_to_pay: 
#                 raise UserError(_(" Please add some amount to Credit lines"))
            
        if credit < (debit + self.paid_amount):
            raise UserError(_("Payment amount exceeds Amount to pay"))
        
        if (self.credit_amount) != (self.paid_amount + diff):
            raise UserError(_("Payment amount exceeds Amount to pay"))
 
        for line in self.credit_line_ids:
            if line.amount_invoice < line.amount_to_pay:
                raise UserError(_("Amount to pay exceeds Invoice amount"))
 
        for line in self.debit_line_ids:
            if line.amount_invoice < line.amount_to_pay:
                raise UserError(_("Amount to pay exceeds Invoice amount"))
 
        if self.credit_line_ids or self.debit_line_ids:
            if self.paid_amount == 0.00:
                for line in self.credit_line_ids:    
                    if line.move_id:                
                        move_line_invoice_id = self.env['account.move.line'].search([('move_id', '=', line.move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
                        for line_id in move_line_invoice_id:
                            if line_id.customer_cr_partial_id.id != line.id:
                                line_id.customer_cr_partial_id = line.id
                    for lines in self.debit_line_ids:
                        if line.amount_reconcile != 0.0:
                            if lines.move_id:
                                move_line_re_invoice_id = self.env['account.move.line'].search([('move_id', '=', lines.move_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
                                for line_id in move_line_re_invoice_id:
                                    if line_id.customer_de_partial_id.id != lines.id:
                                        line_id.customer_de_partial_id = lines.id
                                for line_id in move_line_invoice_id:
                                    if line_id.customer_cr_partial_id.id != line.id:
                                        line_id.customer_cr_partial_id = line.id
                                self.trans_rec_reconcile_payment(move_line_re_invoice_id,move_line_invoice_id)
                        if line.amount_reconcile != 0.0:
                            if lines.payment_id:
                                move_line_payment_id = self.env['account.move.line'].search([('payment_id', '=', lines.payment_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
                                for line_id in move_line_payment_id:
                                    if line_id.customer_de_partial_id.id != lines.id:
                                        line_id.customer_de_partial_id = lines.id
                                for line_id in move_line_invoice_id:
                                    if line_id.customer_cr_partial_id.id != line.id:
                                        line_id.customer_cr_partial_id = line.id
                                self.trans_rec_reconcile_payment(move_line_payment_id,move_line_invoice_id)
                                lines.payment_id.invoice_ids = [(6, 0, [line.move_id.id])]
                if self.payment_difference > 0.00:
                    credit_line_id = False
                    for line in self.credit_line_ids:
                        if line.amount_reconcile >= self.payment_difference:
                            credit_line_id = self.env['customer.multi.payment.credit.line'].browse(line.id)
                            break
                    if not credit_line_id:
                        raise UserError(_("Payment difference exceeds Credit lines amount to pay"))
                    move_line_invoice_id = self.env['account.move.line'].search([('move_id', '=', credit_line_id.move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
                    vals={
                        'name': self.writeoff_label,
                        'debit': 0.0,
                        'credit': self.payment_difference,
                        'account_id': self.writeoff_account_id.id,
                        'journal_id': self.journal_id.id,
                        'partner_id': self.partner_id.id,
                        }
                    move_line_writeoff = move_line_invoice_id._create_writeoff([vals])
                    self.trans_rec_reconcile_payment(move_line_writeoff,move_line_invoice_id)
                    self.writeoff_move_id = move_line_writeoff.move_id
                return self.write({'state': 'posted','account_move': 'No JE Created'})
            if self.paid_amount > 0.00:
                for line in self.credit_line_ids:    
                    if line.move_id:                
                        move_line_invoice_id = self.env['account.move.line'].search([('move_id', '=', line.move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
                        for line_id in move_line_invoice_id:
                            if line_id.customer_cr_partial_id.id != line.id:
                                line_id.customer_cr_partial_id = line.id
                    for lines in self.debit_line_ids:
                        if line.amount_reconcile != 0.0:
                            if lines.move_id:
                                move_line_re_invoice_id = self.env['account.move.line'].search([('move_id', '=', lines.move_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
                                for line_id in move_line_re_invoice_id:
                                    if line_id.customer_de_partial_id.id != lines.id:
                                        line_id.customer_de_partial_id = lines.id
                                for line_id in move_line_invoice_id:
                                    if line_id.customer_cr_partial_id.id != line.id:
                                        line_id.customer_cr_partial_id = line.id
                                self.trans_rec_reconcile_payment(move_line_re_invoice_id,move_line_invoice_id)
                        if line.amount_reconcile != 0.0:
                            if lines.payment_id:
                                move_line_payment_id = self.env['account.move.line'].search([('payment_id', '=', lines.payment_id.id), ('reconciled', '=', False), ('credit', '>', 0)])
                                for line_id in move_line_payment_id:
                                    if line_id.customer_de_partial_id.id != lines.id:
                                        line_id.customer_de_partial_id = lines.id
                                for line_id in move_line_invoice_id:
                                    if line_id.customer_cr_partial_id.id != line.id:
                                        line_id.customer_cr_partial_id = line.id
                                self.trans_rec_reconcile_payment(move_line_payment_id,move_line_invoice_id)
                                lines.payment_id.invoice_ids = [(6, 0, [line.move_id.id])]
                ctx = self._context.copy()
                payment = self.env['account.payment'].create(self.get_all_payment_vals())
                payment.cus_multi_pay_id = self.id
                split_payment = []
                for i in self.credit_line_ids:
                    if i.amount_reconcile != 0.0:
                        split_payment.append({i.move_id: -(i.amount_reconcile)})
#                 for line in split_payment:
#                     amount = list(line.values())[0]
#                     if amount > self.payment_difference:
#                         val = amount + self.payment_difference
#                         split_payment.append({list(line.keys())[0]: (val)})
#                         split_payment.remove({list(line.keys())[0]: (list(split_payment[0].values())[0])})
#                         break
                ctx.update({'split_payment': split_payment})
                payment.with_context(ctx).post()
                
                for line in self.credit_line_ids:    
                    if line.move_id:
                        move_line_invoice_id = self.env['account.move.line'].search([('move_id', '=', line.move_id.id), ('reconciled', '=', False), ('debit', '>', 0)])
                        for line_id in move_line_invoice_id:
                            if line_id.customer_cr_partial_id.id != line.id:
                                line_id.customer_cr_partial_id = line.id
                        move_line_payment_id = self.env['account.move.line'].search([('payment_id', '=', payment.id), ('reconciled', '=', False), ('credit', '>', 0)])
                        for move_line in move_line_payment_id:
                            if line.amount_reconcile != 0.0:
                                self.trans_rec_reconcile_payment(move_line,move_line_invoice_id)
                        
                move_line_id = self.env['account.move.line'].search([('payment_id', '=', payment.id)])
                if move_line_id:
                    self.account_move_id = move_line_id[0].move_id.id
                return self.write({'state': 'posted','account_move': move_line_id[0].move_id.name})
    
    def trans_rec_reconcile_payment(self,line_to_reconcile,payment_line,writeoff_acc_id=False,writeoff_journal_id=False):
        return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)
    
    def open_journal_entries(self):
        payment_ids = self.env["account.move.line"].search([('move_id', '=', self.account_move_id.id)])
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', [x.id for x in payment_ids])],
        }

class CustomerPaymentCreditLine(models.Model):
    _name = "customer.multi.payment.credit.line"

    description = fields.Char('Description')
    move_id = fields.Many2one('account.move', string="Invoice")
    payment_id = fields.Many2one('account.payment', string="Payment")
    amount_invoice = fields.Float('Amount Invoice')
    amount_residual = fields.Float('Residual')
    amount_invoice_dup = fields.Float(related='amount_invoice', string='Amount Invoice', store=True)
    amount_residual_dup = fields.Float(related='amount_residual', string='Residual', store=True)
    inverse_val = fields.Float('Inverse Value', digits=(12, 6))
    invoice_date = fields.Date('Invoice Date')
    amount_to_pay = fields.Float('Amount to pay', default=0.00)
    amount_reconcile = fields.Float('Amount')
    full_reconcile = fields.Boolean('Full Reconcile')
    currency_id = fields.Many2one('res.currency', string='Currency')
    multi_pay_id = fields.Many2one("customer.multi.payment", "Payment ID")
#     currency_rate = fields.Float('Currency Rate', related='multi_pay_id.currency_rate', readonly = True)
    
    @api.onchange('amount_to_pay')
    def onchange_amount_to_pay(self): 
        self.amount_reconcile = self.amount_to_pay
        
    @api.onchange('full_reconcile')
    def onchange_full_reconcile(self):
        if self.full_reconcile:
            self.amount_to_pay = self.amount_residual
        else:
            self.amount_to_pay = 0.0

    @api.model
    def create(self, vals):
        if vals.get('amount_invoice'):
            vals['amount_invoice'] = vals.get('amount_invoice')
        if vals.get('amount_residual'):
            vals['amount_residual'] = vals.get('amount_residual')
        return super(CustomerPaymentCreditLine, self).create(vals)

    def write(self, vals):
        if vals.get('amount_invoice'):
            vals['amount_invoice'] = vals.get('amount_invoice')
        if vals.get('amount_residual'):
            vals['amount_residual'] = vals.get('amount_residual')
        return super(CustomerPaymentCreditLine, self).write(vals)

class CustomerPaymentDebitLine(models.Model):
    _name = "customer.multi.payment.debit.line"

    description = fields.Char('Description')
    move_id = fields.Many2one('account.move', string="Invoice")
    payment_id = fields.Many2one('account.payment', string="Payment")
    amount_invoice = fields.Float('Amount')
    amount_residual = fields.Float('Residual')
    amount_invoice_dup = fields.Float(related='amount_invoice', string='Amount', store=True)
    amount_residual_dup = fields.Float(related='amount_residual', string='Residual', store=True)
    inverse_val = fields.Float('Inverse Value', digits=(12, 6))
    invoice_date = fields.Date('Date')
    amount_to_pay = fields.Float('Amount to pay', default=0.00)
    amount_reconcile = fields.Float('Amount')
    full_reconcile = fields.Boolean('Full Reconcile')
    currency_id = fields.Many2one('res.currency', string='Currency')
    multi_pay_id = fields.Many2one("customer.multi.payment", "Payment ID")
#     currency_rate = fields.Float('Currency Rate', related='multi_pay_id.currency_rate', readonly = True)
    
    @api.onchange('amount_to_pay')
    def onchange_amount_to_pay(self): 
        self.amount_reconcile = self.amount_to_pay
        
    @api.onchange('full_reconcile')
    def onchange_full_reconcile(self):
        if self.full_reconcile:
            self.amount_to_pay = self.amount_residual
        else:
            self.amount_to_pay = 0.0

    @api.model
    def create(self, vals):
        if vals.get('amount_invoice'):
            vals['amount_invoice'] = vals.get('amount_invoice')
        if vals.get('amount_residual'):
            vals['amount_residual'] = vals.get('amount_residual')
        return super(CustomerPaymentDebitLine, self).create(vals)

    def write(self, vals):
        if vals.get('amount_invoice'):
            vals['amount_invoice'] = vals.get('amount_invoice')
        if vals.get('amount_residual'):
            vals['amount_residual'] = vals.get('amount_residual')
        return super(CustomerPaymentDebitLine, self).write(vals)

