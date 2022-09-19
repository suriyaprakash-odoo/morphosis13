from odoo import fields, models, api


class Sales(models.Model):
    _inherit = 'sale.order'

    sub_contract = fields.Boolean("Sub Contract Order")
    subcontract_fraction_ids = fields.One2many("subcontract.fraction", "sale_id", string="Subcontract Fraction Report")
    fractions_total = fields.Monetary('Total', currency_field='currency_id', compute='_compute_fraction_amount')

    def _prepare_purchase_order_data(self, company, company_partner):
        """ Generate purchase order values, from the SO (self)
            :param company_partner : the partner representing the company of the SO
            :rtype company_partner : res.partner record
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        self.ensure_one()
        # find location and warehouse, pick warehouse from company object
        PurchaseOrder = self.env['purchase.order']
        warehouse = company.warehouse_id and company.warehouse_id.company_id.id == company.id and company.warehouse_id or False
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        picking_type_id = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'), ('warehouse_id', '=', warehouse.id)
        ], limit=1)
        if not picking_type_id:
            intercompany_uid = company.intercompany_user_id.id
            picking_type_id = PurchaseOrder.with_user(intercompany_uid)._default_picking_type()
        return {
            'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
            'origin': self.name,
            'partner_id': company_partner.id,
            'picking_type_id': picking_type_id.id,
            'date_order': self.date_order,
            'company_id': company.id,
            'fiscal_position_id': company_partner.property_account_position_id.id,
            'payment_term_id': company_partner.property_supplier_payment_term_id.id,
            'auto_generated': True,
            'auto_sale_order_id': self.id,
            'partner_ref': self.name,
            'currency_id': self.currency_id.id,
            'sub_contract': self.sub_contract,
            'is_internal_purchase': True
        }



    def action_confirm(self):
        res = super(Sales, self).action_confirm()

        contract = self.env['subcontract.process'].search([('sale_order_id', '=', self.id)], limit=1)
        stock_picking_id = self.env['stock.picking'].search([('origin', '=', self.name)], limit=1)
        if stock_picking_id and self.sub_contract:
            if contract and contract.type == 'internal':
                stock_picking_id.sub_contract_order = self.sub_contract
                stock_picking_id.is_internal_purchase = True
                stock_picking_id.sub_type = contract.type
            else:
                stock_picking_id.sub_contract_order = self.sub_contract
                stock_picking_id.sub_type = contract.type

        purchase_obj = self.env['purchase.order'].search([('origin', '=', self.name)],limit=1)
        if purchase_obj:
            purchase_obj.sub_contract = self.sub_contract
            if contract:
                contract.purchase_order_id = purchase_obj.id

        return res

    def _compute_fraction_amount(self):
        for sale in self:
            total_price = 0.0
            if sale.subcontract_fraction_ids:
                for line in sale.subcontract_fraction_ids:
                    total_price += line.price_subtotal
                    sale.fractions_total = total_price
            else:
                sale.fractions_total = 0.0

    def _create_invoices(self, grouped=False, final=False):
        """Create invoice note lines with notes from the sale order"""
        invoice_ids = super()._create_invoices(
            grouped=grouped, final=final
        )
        if invoice_ids:
            for rec in self:
                sub_contract = self.env["subcontract.process"].search([('sale_order_id', '=', rec.id)], limit=1)
            if sub_contract:
                sub_contract.state = 'done'
                if sub_contract.type == 'outsource':
                    for rec in sub_contract.container_ids:
                        rec.state = 'sold'
                else:
                    if self.partner_id.parent_id:
                        company_id = self.env["res.company"].search([('partner_id', '=', self.partner_id.parent_id.id)])
                        for rec in sub_contract.container_ids:
                            rec.state = 'sold'
                            rec.related_company_id = company_id.id
                    elif self.env["res.company"].search([('partner_id', '=', self.partner_id.id)]):
                        for rec in sub_contract.container_ids:
                            rec.state = 'sold'
                            rec.related_company_id = self.env["res.company"].search([('partner_id', '=', self.partner_id.id)]).id
                    else:
                        for rec in sub_contract.container_ids:
                            rec.state = 'sold'
        return invoice_ids


class SubContractReport(models.Model):
    _name = 'subcontract.fraction'

    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char('Description')
    product_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float('Unit Price')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order ref')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.description = str(self.product_id.name) + ' - ' + str(self.product_id.product_template_attribute_value_ids.name)
            self.price_unit = self.product_id.lst_price
            self.product_uom = self.product_id.uom_id.id

    @api.depends('product_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit
