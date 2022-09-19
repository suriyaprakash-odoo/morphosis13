# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class LoadTruck(models.TransientModel):
	_name = 'load.truck'

	sale_logistics_weight_at_entry = fields.Float('Truck weight at entry(Kg)', digits=(12,4))
	sale_logistics_entry_date_time = fields.Datetime('Truck arrival time', default=fields.Datetime.now)
	truck_licence_plate = fields.Char('Truck Number')

	def load_truck(self):
		stock_picking = self.env.context.get('active_id')
		stock_picking_id = self.env['stock.picking'].browse(stock_picking)

		if stock_picking_id:
			stock_picking_id.write({
				'sale_logistics_weight_at_entry' : self.sale_logistics_weight_at_entry,
				'sale_logistics_entry_date_time' : self.sale_logistics_entry_date_time,
				'truck_licence_plate' : self.truck_licence_plate,
				'incoming_truck_registered' : True,
				'state' : 'load_unload',
				# 'task_timer':True
				})
			stock_picking_id.truck_notification()
			
			if stock_picking_id.picking_type_id.sequence_code == 'OUT':
				sale_obj = self.env['sale.order'].search([('name', '=', str(stock_picking_id.origin))])
				if sale_obj:
					logistics_obj = self.env['logistics.management'].search([('sales_origin', '=', sale_obj.id),('status' , '=' , 'approved')], limit=1)
					if logistics_obj:
						logistics_obj.reception_date = datetime.now().date()

		return {'type': 'ir.actions.act_window_close'}