# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class UpdateContainerDetails(models.TransientModel):
	_name = 'update.container.details'

	delivery_licence_plate = fields.Char('Registraion of container')
	customs_seal_number = fields.Char('Customs Seal Number')

	def update_container_details(self):
		logistics = self.env.context.get('active_id')
		logistics_id = self.env['logistics.management'].browse(logistics)

		if logistics_id:
			logistics_id.write({
				'delivery_licence_plate' : self.delivery_licence_plate,
				'customs_seal_number' : self.customs_seal_number
				})

			stock_picking_id = self.env['stock.picking'].search([('project_entry_id' , '=' , logistics_id.origin.id)])
			print(stock_picking_id,'---',logistics_id.origin)
			if stock_picking_id:
				stock_picking_id.write({
					'purchase_truck_container_number' : self.delivery_licence_plate,
					'purchase_container_seal_number' : self.customs_seal_number
					})

		return {'type': 'ir.actions.act_window_close'}