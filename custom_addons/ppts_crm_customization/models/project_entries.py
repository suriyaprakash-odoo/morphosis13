from odoo import fields, models, api, _

class ProjectEntriesLine(models.Model):
    _inherit = 'project.entries.line'

    purchase_order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order line_ref")
    line_origin = fields.Char('Origin',default='project')

    # def create(self,vals):
    # 	res = super(ProjectEntriesLine, self).create(vals)
    # 	for record in res:
    # 		if not record.line_origin == 'crm':
    # 			project_product_line_list = []
    # 			project_product_line_list.append((0, 0, {
    # 					'product_id': record.product_id.id,
    # 					'description': record.name or '',
    # 					'quantity': record.product_qty,
    # 					'uom_id': record.product_uom.id,
    # 					'price_per_ton': record.price_unit,
    # 					'is_malus': record.is_malus,
    # 					# 'price': record.price,
    # 					'offer_price': record.offer_price,
    # 					'return_price': record.malus,
    # 					'charge_malus': record.charge_malus,
    # 					'malus_demand': record.malus_demand,
    # 					# 'expexted_margin_percentage': record.expexted_margin_percentage,
    # 					'computed_margin_percentage': record.computed_margin_percentage,
    # 					'line_origin':record.line_origin
				# 	}))
    # 			record.project_entry_id.origin.opportunity_id.product_lines = project_product_line_list
    # 	return res

    def write(self,vals):
        res = super(ProjectEntriesLine, self).write(vals)

        if vals.get('product_qty'):

            crm_sql_query = '''
                update crm_product_line set quantity = %s where id = %s
            '''
            po_sql_query = '''
                update purchase_order_line set product_qty = %s where id = %s
            '''
            if self.purchase_order_line_id:
                self.env.cr.execute(po_sql_query, (self.product_qty,self.purchase_order_line_id.id,))

                if self.purchase_order_line_id.crm_product_line_id:
                    self.env.cr.execute(crm_sql_query, (self.product_qty,self.purchase_order_line_id.crm_product_line_id.id,))

        if vals.get('offer_price'):

            po_sql_query = '''
                update purchase_order_line set price_unit = %s where id = %s
            '''
            crm_sql_query = '''
                update crm_product_line set offer_price = %s where id = %s
            '''

            if self.purchase_order_line_id:
                self.env.cr.execute(po_sql_query, (self.offer_price,self.purchase_order_line_id.id,))
                self.purchase_order_line_id.price_subtotal = self.purchase_order_line_id.price_unit * self.purchase_order_line_id.product_qty

                if self.purchase_order_line_id.crm_product_line_id:
                    self.env.cr.execute(crm_sql_query, (self.offer_price,self.purchase_order_line_id.crm_product_line_id.id,))

        if vals.get('malus_demand'):

            po_sql_query = '''
                update purchase_order_line set price_unit = %s where id = %s
            '''
            crm_sql_query = '''
                update crm_product_line set malus_demand = %s where id = %s
            '''

            if self.purchase_order_line_id:
                self.env.cr.execute(po_sql_query, (float('-'+str(self.malus_demand)),self.purchase_order_line_id.id,))
                self.purchase_order_line_id.price_subtotal = self.purchase_order_line_id.price_unit * self.purchase_order_line_id.product_qty

                if self.purchase_order_line_id.crm_product_line_id:
                    self.env.cr.execute(crm_sql_query, (self.malus_demand,self.purchase_order_line_id.crm_product_line_id.id,))

        return res