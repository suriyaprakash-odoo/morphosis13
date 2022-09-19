from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total','order_line.price_subtotal','amount_from_offer')
    def _amount_all(self):
        for order in self:
        	if not order.opportunity_id:
	            amount_untaxed = amount_tax = 0.0
	            for line in order.order_line:
	            	amount_untaxed += line.price_subtotal
	            	amount_tax += line.price_tax
	            order.update({
	                'amount_untaxed': order.currency_id.round(amount_untaxed),
                    'amount_from_offer': order.currency_id.round(amount_untaxed),
	                'amount_tax': order.currency_id.round(amount_tax),
	                'amount_total': amount_untaxed + amount_tax,
	            })
	        else:
	        	amount_untaxed = amount_tax = 0.0
	        	for line in order.order_line:
	        		amount_untaxed += line.price_subtotal
	        		amount_tax += line.price_tax
	        	order.update({
	                'amount_untaxed': order.currency_id.round(amount_untaxed),
                    'amount_from_offer': order.currency_id.round(amount_untaxed),
	                'amount_tax': order.currency_id.round(amount_tax),
	                'amount_total': order.currency_id.round(amount_untaxed) + amount_tax,
	            })


    opportunity_id = fields.Many2one("crm.lead",string="Opportunity")

    amount_from_offer =fields.Monetary(string='Offered Amount', readonly=True, tracking=True, store=True, currency_field='currency_id', compute='_amount_all')

    @api.onchange('partner_id')
    def onchange_partner_in_picking(self):
        if self.partner_id:
            if self.partner_id.short_code:
                short_code = self.partner_id.short_code + '/'
            else:
                short_code = ''
            if self.partner_id.ref:
                ref = self.partner_id.ref + '/'
            else:
                ref = ''
            self.partner_ref = ref + short_code + str(self.partner_id.lot_sequence_number)

    def write(self,vals):
        res = super(PurchaseOrder, self).write(vals)
        

        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    crm_product_line_id = fields.Many2one('crm.product.line', string="CRM Product Line ref")
    line_origin = fields.Char('Origin',default='purchase')

    # def create(self,vals):
    #     res = super(PurchaseOrderLine, self).create(vals)

    #     for record in res:
    #         if not record.line_origin == 'project':
    #             if record.crm_product_line_id:
    #                 crm_product_line_list = []
    #                 crm_product_line_list.append((0, 0, {
    #                     'product_id': record.crm_product_line_id.product_id.id,
    #                     'name': record.crm_product_line_id.description or '',
    #                     'product_qty': record.crm_product_line_id.quantity,
    #                     'product_uom': record.crm_product_line_id.uom_id.id,
    #                     'price_unit': record.crm_product_line_id.price_per_ton,
    #                     'is_malus': record.crm_product_line_id.is_malus,
    #                     'price': record.crm_product_line_id.price,
    #                     'offer_price': record.crm_product_line_id.offer_price,
    #                     'margin_class': record.crm_product_line_id.margin_class,
    #                     'malus': record.crm_product_line_id.return_price,
    #                     'charge_malus': record.crm_product_line_id.charge_malus,
    #                     'malus_demand': record.crm_product_line_id.malus_demand,
    #                     'expexted_margin_percentage': record.crm_product_line_id.expexted_margin_percentage,
    #                     'computed_margin_percentage': record.crm_product_line_id.computed_margin_percentage,
    #                     'line_origin':record.line_origin,
    #                     'purchase_order_line_id':record.id
    #                 }))

    #                 print(crm_product_line_list)

    #                 project_obj = self.env['project.entries'].search([('origin' , '=' , record.order_id.id)])
    #                 if project_obj:
    #                     project_obj.project_entry_ids = crm_product_line_list
    #             else:
    #                 po_product_line_list = []
    #                 po_product_line_list.append((0, 0, {
    #                             'product_id':record.product_id.id,
    #                             'name':record.name or '',
    #                             'product_qty':record.product_qty,
    #                             'product_uom':record.product_uom.id,
    #                             'price_unit':record.price_unit,
    #                             'taxes_id':[(6, 0, record.taxes_id.ids)],
    #                             'price_subtotal':record.price_subtotal,
    #                             'offer_price':record.price_unit * record.product_qty,
    #                             'purchase_order_line_id':record.id,
    #                             'line_origin':record.line_origin
    #                             }))

    #                 print(po_product_line_list)

    #                 project_obj = self.env['project.entries'].search([('origin' , '=' , record.order_id.id)])
    #                 if project_obj:
    #                     project_obj.project_entry_ids = po_product_line_list

    #     return res

    def write(self,vals):
        res = super(PurchaseOrderLine, self).write(vals)

        if vals.get('product_qty'):
            crm_sql_query = '''
                update crm_product_line set quantity = %s where id = %s
            '''

            project_sql_query = '''
                update project_entries_line set product_qty = %s where id = %s
            '''

            if self.crm_product_line_id:
                for crm_line_obj in self.crm_product_line_id:
                    self.env.cr.execute(crm_sql_query, (self.product_qty,crm_line_obj.id,))

            project_line_obj = self.env['project.entries.line'].search([('purchase_order_line_id' , '=' , self.id)])
            if project_line_obj:
                for line_obj in project_line_obj:
                    self.env.cr.execute(project_sql_query, (self.product_qty,line_obj.id,))
                    line_obj.project_entry_id.quoted_price = self.order_id.amount_from_offer
                    line_obj.project_entry_id.target_price = self.order_id.amount_from_offer


        if vals.get('price_unit'):
            if self.crm_product_line_id:

                for crm_line_obj in self.crm_product_line_id:

                    if not crm_line_obj.is_malus:
                        crm_sql_query = '''
                            update crm_product_line set offer_price = %s where id = %s
                        '''

                        self.env.cr.execute(crm_sql_query, (self.price_unit,crm_line_obj.id,))
                    else:
                        crm_sql_query = '''
                            update crm_product_line set malus_demand = %s where id = %s
                        '''

                        self.env.cr.execute(crm_sql_query, (self.price_unit,crm_line_obj.id,))

            project_line_obj = self.env['project.entries.line'].search([('purchase_order_line_id' , '=' , self.id)])
            if project_line_obj:
                for line_obj in project_line_obj:
                    if not self.crm_product_line_id.is_malus:
                        project_sql_query = '''
                            update project_entries_line set offer_price = %s where id = %s
                        '''
                        self.env.cr.execute(project_sql_query, (self.price_unit,line_obj.id,))
                        line_obj.project_entry_id.quoted_price = self.order_id.amount_from_offer
                        line_obj.project_entry_id.target_price = self.order_id.amount_from_offer
                    else:
                        project_sql_query = '''
                            update project_entries_line set malus_demand = %s where id = %s
                        '''
                        self.env.cr.execute(project_sql_query, (self.price_unit,line_obj.id,))
                        line_obj.project_entry_id.quoted_price = self.order_id.amount_from_offer
                        line_obj.project_entry_id.target_price = self.order_id.amount_from_offer

        return res