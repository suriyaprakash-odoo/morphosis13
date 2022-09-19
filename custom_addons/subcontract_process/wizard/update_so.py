# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_
from odoo.exceptions import UserError

class UpdateSO(models.TransientModel):
	_name = 'update.sales'

	@api.model
	def default_get(self, fields_name):
		res = super(UpdateSO, self).default_get(fields_name)
		if self._context.get('active_id'):
			sale_order_obj = self.env['sale.order'].search([('id' , '=' , int(self._context.get('active_id')))])
			product_line_list = []
			if sale_order_obj.order_line:
				product_line_list = [(0, 0, {
					'product_id':record.product_id.id,
					'quoted_price':record.price_unit,
					'final_price':0.00,
					'id_sale_order_line':record.id or ''
					})for record in sale_order_obj.order_line]

				res.update({'sale_line_ids': product_line_list})
			res.update({'so_order_id' : sale_order_obj.id})
		return res

	so_order_id = fields.Many2one('sale.order', string="Sale Order", readonly=1)
	sale_line_ids = fields.One2many('update.so.line','sale_line_id', string="Update Line ref")

	def update_sale_order(self):
		if self.sale_line_ids:
			total_price = 0.00
			for line in self.sale_line_ids:
				if line.final_price:
					total_price += line.final_price
					line.id_sale_order_line.price_unit = line.final_price
		return {'type': 'ir.actions.act_window_close'}


class UpdatePriceLine(models.TransientModel):
	_name = 'update.so.line'

	product_id = fields.Many2one('product.product', string="Product")
	quoted_price = fields.Float('Quoted Price')
	final_price = fields.Float('Final Price')
	id_sale_order_line = fields.Many2one('sale.order.line', string='Order Line ref')
	sale_line_id = fields.Many2one('update.sales', string="Update Line ref")