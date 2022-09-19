from odoo import fields, models, api, _


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    # @api.model
    # def default_get(self, fields_name):
    #     res = super(AccountInvoice, self).default_get(fields_name)
    #     res.update({'approver_id': self.env.user.approver_id.id})
    #     return res

    approval_required = fields.Boolean("Approval Required?", compute='_approval_required')
    state = fields.Selection(selection_add=[('approval', 'Waiting for Approval')])
    approver_id = fields.Many2one("res.users", string="Person to Approve")

    # def _find_approver(self):
    #     for rec in self:
    #         approver_id = False
    #         if rec.invoice_origin:
    #             po_id = self.env['purchase.order'].search([('name','=',rec.invoice_origin)])
    #             if po_id:
    #                approver_id = po_id.user_id.id
    #         rec.update({
    #             'approver_id': approver_id,
    #         })


    @api.depends('amount_total')
    def _approval_required(self):
        for rec in self:
            approval_required = False
            if rec.type=='in_invoice':
                if rec.amount_total > rec.company_id.invoice_threshold:
                   approval_required = True
            rec.update({
                'approval_required': approval_required,
            })

    def send_for_approval(self):
        template_id = self.env.ref('bills_approval.template_send_for_approval')
        rec_company = self.company_id.id
        approver_company = self.approver_id.company_id.id
        cids = approver_company
        if rec_company != approver_company:
            cids = str(rec_company)+','+str(approver_company)
        if self.approver_id.login:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            base_url += '/web#cids=%s&id=%d&view_type=form&model=%s' % (cids,self.id, self._name)
            template_id.with_context({'url':base_url}).send_mail(self.id, force_send=True)
        self.state = 'approval'

    def approve_bill(self):
        self.action_post()

    @api.model
    def create(self, vals):
        lines = super(AccountInvoice, self).create(vals)

        #adding notes to credit notes from purchase order
        if lines.invoice_origin:
            purchase_order = self.env['purchase.order'].sudo().search([('name','=',lines.invoice_origin)],limit=1)
            if purchase_order:
                line_ids = []
                for i in purchase_order.order_line:
                    if i.display_type=="line_note":
                        line_ids.append((0, 0, {
                            'name':i.name,
                            'display_type':'line_note',
                        }))
                lines.invoice_line_ids = line_ids
        return lines
    