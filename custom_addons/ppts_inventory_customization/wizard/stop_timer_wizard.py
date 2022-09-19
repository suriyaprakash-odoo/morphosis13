# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from odoo.exceptions import AccessError, UserError, ValidationError

class StopTimer(models.TransientModel):
	_name = 'stop.timer'

	@api.model
	def default_get(self, fields_name):
		res = super(StopTimer, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
			sale_obj = self.env['sale.order'].search([('name', '=', stock_picking_id.origin)])
			
			container_line_list = []
			if stock_picking_id.move_ids_without_package:
				for picking_line in stock_picking_id.move_ids_without_package:
					if picking_line.container_ids:
						for container in  picking_line.container_ids:
							container_line_list.append(container.id)				

			res.update({'picking_container_ids': container_line_list})
			res.update({'sale_order_id' : sale_obj.id})
			res.update({'shipment_id' : stock_picking_id.id})

		return res

	shipment_id = fields.Many2one('stock.picking', string='Shipping ID')
	sale_order_id = fields.Many2one('sale.order', string='Sale Order')
	manual_time = fields.Float("Total Time(Minutes)")

	picking_container_ids = fields.Many2many('stock.container','picking_container_key', string='Containers in Picking List')
	loaded_container_ids = fields.Many2many('stock.container','loading_container_key', string='Loaded container List')

	def stop_timer(self):
		if self.shipment_id:
			self.shipment_id.task_timer = False

		# view_id = self.env.ref('ppts_inventory_customization.view_stop_timer').id
		# return {
  #           'name': ('Validate Shipment'),
  #           'type': 'ir.actions.act_window',
  #           'view_type': 'form',
  #           'view_mode': 'form',
  #           'res_model': 'stop.timer',
  #           'views': [(view_id, 'form')],
  #           'view_id': view_id,
  #           'target': 'new',
  #           'res_id': self.ids[0],
  #       }

	def validate_picking(self):
		self.shipment_id.task_timer = False
		if self.manual_time:
			self.shipment_id.manual_time = self.manual_time
		if self.shipment_id.total_time or self.shipment_id.manual_time:
			if self.picking_container_ids:
				if self.loaded_container_ids:				
					picking_container_list = []
					load_container_list = []
					final_container_list = []
					for pc in self.picking_container_ids:
						picking_container_list.append(pc.id)
					for lc in self.loaded_container_ids:
						load_container_list.append(lc.id)

					common = list(set.intersection(set(picking_container_list),set(load_container_list)))

					picking_container_list.extend(load_container_list)
					final_container_list = [i for i in picking_container_list if i not in common]

					if len(final_container_list) == 0:
						# self.shipment_id.state = 'production'
						# self.shipment_id.task_timer = False
						self.shipment_id.load_validated = True
						# self.shipment_id.state = 'release_lorry'
						# self.shipment_id.is_unloaded = True
					else:
						container_name = []
						for rec in final_container_list:
							con_obj = self.env['stock.container'].browse(int(rec))
							container_name.append(con_obj.name)
						raise UserError(_('There are some mismatched container which are as follows: %s') % container_name)
				else:
					raise UserError('Please Select loaded container list before validation!')
			else:
				raise UserError('Please Update the container details!')
		else:
			raise UserError('Please update the loading/unloading time of truck')
			
		return {'type': 'ir.actions.act_window_close'}


class StopTimerReuse(models.TransientModel):
	_name = 'stop.timer.reuse'

	@api.model
	def default_get(self, fields_name):
		res = super(StopTimerReuse, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))

			container_line_list = []
			move_line = self.env["stock.move.line"].search([('picking_id', '=', stock_picking_id.id)])
			for line in move_line:
				container_line_list.append(line.id)

			res.update({'loaded_container_ids': container_line_list})
			res.update({'shipment_id': stock_picking_id.id})

		return res

	shipment_id = fields.Many2one('stock.picking', string='Shipping ID')
	# picking_container_ids = fields.Many2many('stock.container', 'picking_container_key', string='Containers in Picking List')
	loaded_container_ids = fields.Many2many('stock.move.line', string='Container List')

	def validate_picking(self):
		self.shipment_id.task_timer = False
		self.shipment_id.load_validated = True
		return {'type': 'ir.actions.act_window_close'}
