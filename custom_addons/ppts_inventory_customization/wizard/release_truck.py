# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError

class ReleaseContainers(models.TransientModel):
	_name = 'release.container'

	@api.model
	def default_get(self, fields_name):
		res = super(ReleaseContainers, self).default_get(fields_name)
		print(self._context.get('active_id'))
		if self._context.get('active_id'):
			shipping_obj = self.env['stock.picking'].search([('id' , '=' , int(self._context.get('active_id')))])
			res.update({'weight_at_entry': shipping_obj.weight_at_entry})
			if shipping_obj.move_ids_without_package:
				res.update({'bsd_annexe': shipping_obj.move_ids_without_package[0].bsd_annexe})
			if shipping_obj.move_line_ids_without_package:
				res.update({'bsd_annexe': shipping_obj.move_ids_without_package[0].bsd_annexe})
		return res

	exit_date_time = fields.Datetime('Truck exit time', default=fields.Datetime.now)
	weight_at_entry = fields.Float('Truck Weight at entry(Kg)', digits=(12,4))
	weight_at_exit = fields.Float('Truck weight at exit(Kg)', digits=(12,4))
	bsd_annexe = fields.Selection([
		('bsd' , 'BSD'),
		('annexe7' , 'Annexe7')
	],string='BSD/Annexe7')

	def print_bsd_report(self):
		stock_picking = self.env.context.get('active_id')
		stock_picking_id = self.env['stock.picking'].browse(stock_picking)
		if stock_picking_id.picking_type_id.sequence_code == 'IN':
			logistics_obj = self.env['logistics.management'].search([('origin' , '=' , stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')],limit=1)
			return self.env.ref('ppts_logistics.report_bsd').report_action(logistics_obj)

		if stock_picking_id.picking_type_id.sequence_code == 'OUT':
			sales_obj = self.env['sale.order'].search([('name' , '=' , stock_picking_id.origin)])
			logistics_obj = self.env['logistics.management'].search([('sales_origin' , '=' , sales_obj.id),('status' , '=' , 'approved')],limit=1)
			return self.env.ref('ppts_logistics.report_bsd').report_action(logistics_obj)

	def print_annux_report(self):
		stock_picking = self.env.context.get('active_id')
		stock_picking_id = self.env['stock.picking'].browse(stock_picking)
		if stock_picking_id.picking_type_id.sequence_code == 'IN':
			logistics_obj = self.env['logistics.management'].search([('origin' , '=' , stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')],limit=1)
			return self.env.ref('ppts_logistics.report_annux').report_action(logistics_obj)

		if stock_picking_id.picking_type_id.sequence_code == 'OUT':
			sales_obj = self.env['sale.order'].search([('name' , '=' , self.picking_id.origin)])
			logistics_obj = self.env['logistics.management'].search([('sales_origin' , '=' , sales_obj.id),('status' , '=' , 'approved')],limit=1)
			return self.env.ref('ppts_logistics.report_annux').report_action(logistics_obj)

	def release_container(self):

		if not self.weight_at_exit > self.weight_at_entry:
			stock_picking = self.env.context.get('active_id')
			stock_picking_id = self.env['stock.picking'].browse(stock_picking)
			diff = self.exit_date_time - stock_picking_id.entry_date_time
			real_duration = round(diff.total_seconds() / 60.0, 2)
			if stock_picking_id:
				stock_picking_id.write({
					'exit_date_time' : self.exit_date_time,
					'weight_at_exit' : self.weight_at_exit,
					'state' : 'reception',
					'real_duration':real_duration,
					})
				# if stock_picking_id.move_ids_without_package:
				# 	for move_id in stock_picking_id.move_ids_without_package:
				# 		move_id.update({'bsd_annexe':self.bsd_annexe})
				stock_picking_id.project_entry_id.status = 'wip'	

				fifteen_days = date.today() + timedelta(days=15)
				stock_picking_id.project_entry_id.fifteen_days_date = fifteen_days

				logistics_obj = self.env['logistics.management'].search([('origin' , '=' , stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')], limit=1)
				if logistics_obj:
					logistics_obj.status = 'delivered'

			return {'type': 'ir.actions.act_window_close'}
		else:
			raise UserError('Truck exit weight is greater than truck entry weight')