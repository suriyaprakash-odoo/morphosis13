# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_
from odoo.exceptions import UserError

class UpdatePrice(models.TransientModel):
	_name = 'update.purchase'

	@api.model
	def default_get(self, fields_name):
		res = super(UpdatePrice, self).default_get(fields_name)
		if self._context.get('active_id'):
			purchase_order_obj = self.env['purchase.order'].search([('id' , '=' , int(self._context.get('active_id')))])
			product_line_list = []
			if purchase_order_obj.order_line:
				product_line_list = [(0, 0, {
					'product_id':record.product_id.id,
					'product_quantity':record.product_qty,
					'quoted_price':record.price_subtotal,
					'final_price':0.00,
					'id_purchase_order_line':record.id or ''
					})for record in purchase_order_obj.order_line]

				res.update({'purchase_line_ids': product_line_list})
			res.update({'purchase_order_id' : purchase_order_obj.id})

		return res

	purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
	purchase_line_ids = fields.One2many('update.purchase.line','purchase_line_id', string="Update Line ref")

	def update_purchase_order(self):
		# if self.purchase_order_id.invoice_count > 0:
		# 	raise UserError(_('Invoice is already created,So you can not update Price!'))
		# else:
		if self.purchase_line_ids:
			total_price = 0.00
			for line in self.purchase_line_ids:
				if line.final_price:
					total_price += line.final_price
					line.id_purchase_order_line.price_unit = line.final_price / line.product_quantity
		if self.purchase_order_id:
			project_obj = self.env['project.entries'].search([('origin' , '=' , self.purchase_order_id.id)])
			if project_obj:
				project_obj.target_price = total_price
			if self.purchase_order_id.project_entry_id:
				project_purchase_obj = self.env['project.purchase.orders'].search([('purchase_id', '=', self.purchase_order_id.id)])
				if project_purchase_obj:
					project_purchase_obj.amount = total_price

		return {'type': 'ir.actions.act_window_close'}


class UpdatePriceLine(models.TransientModel):
	_name = 'update.purchase.line'

	product_id = fields.Many2one('product.product', string="Product")
	product_quantity = fields.Float('Qunatity')
	quoted_price = fields.Float('Quoted Price')
	final_price = fields.Float('Final Price')
	id_purchase_order_line = fields.Many2one('purchase.order.line', string='Order Line ref')
	purchase_line_id = fields.Many2one('update.purchase', string="Update Line ref")
