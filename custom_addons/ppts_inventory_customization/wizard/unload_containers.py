# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class UnloadContainers(models.TransientModel):
	_name = 'unload.container'


	# actual_delivery = fields.Date('Actual date of delivery')
	weight_at_entry = fields.Float('Truck weight at entry(Kg)', digits=(12,4))
	entry_weight_uom_id = fields.Many2one('uom.uom','Weight Unit')
	entry_date_time = fields.Datetime('Truck arrival time', default=fields.Datetime.now)
	license_plate_number = fields.Char('License Plate Number')

	transporter = fields.Many2one("res.partner", "Transporter")


	@api.model
	def default_get(self, fields_name):
		res = super(UnloadContainers, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
			
			if stock_picking_id:
				logistics_obj = self.env['logistics.management'].search([('origin', '=', stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')], limit=1)

				if logistics_obj:
					res.update({'transporter' : logistics_obj.partner_id.id if logistics_obj.partner_id else False})

		return res


	def unload_container(self):

		stock_picking = self.env.context.get('active_id')

		stock_picking_id = self.env['stock.picking'].browse(stock_picking)

		def date_by_adding_business_days(from_date, add_days):
		    business_days_to_add = add_days
		    current_date = from_date
		    while business_days_to_add > 0:
		        current_date += timedelta(days=1)
		        weekday = current_date.weekday()
		        if weekday >= 5: # sunday = 6
		            continue
		        business_days_to_add -= 1
		    return current_date
		fifteen_days_date = date_by_adding_business_days(datetime.now().date(), 15)
		
		if stock_picking_id:
			stock_picking_id.write({
				# 'actual_delivery' : self.actual_delivery,
				'weight_at_entry' : self.weight_at_entry,
				'entry_weight_uom_id' : self.entry_weight_uom_id,
				'entry_date_time' : self.entry_date_time,
				'license_plate_number' : self.license_plate_number,
				'state' : 'load_unload',
				'transporter_partner_id': self.transporter.id if self.transporter else False,
				})

			stock_picking_id.project_entry_id.fifteen_days_date = fifteen_days_date
			stock_picking_id.project_entry_id.status = 'reception'

			stock_picking_id.truck_notification()		

			if stock_picking_id.project_entry_id:
				logistics_obj = self.env['logistics.management'].search([('origin', '=', stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')], limit=1)
				if logistics_obj:
					logistics_obj.reception_date = datetime.now().date()
					logistics_obj.partner_id = self.transporter.id if self.transporter else False

		return {'type': 'ir.actions.act_window_close'}