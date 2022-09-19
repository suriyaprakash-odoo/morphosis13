# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class SalePickingList(models.TransientModel):
	_name = 'sale.picking.list'

	@api.model
	def default_get(self, fields_name):
		res = super(SalePickingList, self).default_get(fields_name)
		if self._context.get('default_product_id'):
			res.update({'product_id': self._context.get('default_product_id')})

		if self._context.get('default_weight'):
			res.update({'sales_weight':self._context.get('default_weight')})

		return res

	sales_weight = fields.Float('Sales Weight(Kg)')
	container_ids = fields.Many2many('stock.container', string="Container")
	product_id = fields.Many2one('product.product', string="Product")
	actual_weight = fields.Float('Actual Weight(Kg)')

	@api.onchange('product_id')
	def onchage_product_id(self):
		if self.product_id:
			res={'domain':{'container_ids': "[('id', '=', False)]"}}
			if self.product_id.container_product_ids:
				containers_list = []
				for line in self.product_id.container_product_ids:
					containers_list.append(line.container_id.id)
				if len(containers_list) > 1:
					if containers_list:
						res['domain']['container_ids'] = "[('id', 'in', %s)]" % containers_list
					else:
						res['domain']['container_ids'] = []
				else:

					if containers_list:
						res['domain']['container_ids'] = "[('id', '=', %s)]" % containers_list[0]
					else:
						res['domain']['container_ids'] = []

		return res

	@api.onchange('container_ids')
	def onchange_actual_weight(self):
		if self.container_ids:
			self.actual_weight = 0.0
			for rec in self.container_ids:
				self.actual_weight += rec.net_weight



	def add_containers(self):
		sale_order_line = self.env.context.get('active_id')

		sale_order_line_obj = self.env['sale.order.line'].browse(sale_order_line)
		
		if sale_order_line_obj:
			
			sale_order_line_obj.container_id = self.container_ids

		return {'type': 'ir.actions.act_window_close'}