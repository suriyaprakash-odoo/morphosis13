# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class UnloadTruck(models.TransientModel):
	_name = 'unload.truck'

	@api.model
	def default_get(self, fields_name):
		res = super(UnloadTruck, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
			if stock_picking_id:
				res.update({'actual_containers' : stock_picking_id.no_of_container})
				res.update({'container_seal_number' : stock_picking_id.purchase_container_seal_number})
				res.update({'truck_container_number' : stock_picking_id.purchase_truck_container_number})
			if stock_picking_id.project_entry_id:
				project_entry_line_obj = self.env['project.entries.line'].search([('project_entry_id' , '=' , stock_picking_id.project_entry_id.id)])
				container_line_list = []
				for project_line in  project_entry_line_obj:
					container_line_obj = self.env['container.type.line'].search([('project_line_id' , '=' , project_line.id)])
					if container_line_obj:
						for record in container_line_obj:
							container_line_list.append(
								(0, 0, {
								'container_type_id':record.container_type_id.id,
								'container_length':record.container_length,
								'container_width':record.container_width,
								'container_height':record.container_height,
								'final_container_height':record.final_container_height,
								'container_count':record.container_count,
								'line_id':record.id
								})
							)

					res.update({'container_details_line_ids': container_line_list})

		return res

	actual_containers = fields.Integer('Actual Container count')
	received_containers = fields.Integer('Total No of containers arrived')
	container_seal_number = fields.Char('Container Seal Number')
	truck_container_number = fields.Char('Truck Container Number')
	is_container_seal_match = fields.Boolean("Is container Seal Number matched?")
	is_truck_container_number_match = fields.Boolean("Incohérence comptage?")
	worker_ids = fields.Many2many('hr.employee', string="Workers", domain="[('is_worker','=', True)]")
	manual_time = fields.Float("Total Time(Minutes)")
	container_details_line_ids = fields.One2many('container.details.line','container_details_line_id', string="Unload truck line ref")

	is_truck_container_number_match_mail_sent = fields.Boolean(default=False)
	mail_status = fields.Boolean(default=False)

	@api.onchange("received_containers")
	def _onchange_received_containers(self):
		if self.received_containers !=self.actual_containers:
			self.is_truck_container_number_match = True
		else:
			self.is_truck_container_number_match = False
	
	def action_send_container_mismatch(self):
		'''
        This function opens a window to compose an email, with the edit send mismatch intimation template message loaded by default
        '''
		
		stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
		stock_picking_id.ensure_one()
		ir_model_data = stock_picking_id.env['ir.model.data']
		try:
			# template_id = ir_model_data.get_object_reference('ppts_inventory_customization', 'email_template_container_mismatched')
			template_id = self.env.ref('ppts_inventory_customization.email_template_container_mismatched')
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False
		ctx = dict(stock_picking_id.env.context or {})

		ctx.update({
			'default_model': 'stock.picking',
			'default_res_id': stock_picking_id.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'model_description': 'Mismatch of received containers',
			'mark_so_as_sent': True
		})

		template_id.with_context(ctx).send_mail(stock_picking_id.id, force_send=True)

		self.is_truck_container_number_match_mail_sent = True
		self.mail_status = True
		return {
			"type": "ir.actions.do_nothing",
		}

			

	def stop_timer(self):
		stock_picking = self.env.context.get('active_id')
		stock_picking_id = self.env['stock.picking'].browse(stock_picking)

		if stock_picking_id:
			stock_picking_id.task_timer = False

		# view_id = self.env.ref('ppts_inventory_customization.view_unload_truck').id
		# return {
  #           'name': ('Unload Truck'),
  #           'type': 'ir.actions.act_window',
  #           'view_type': 'form',
  #           'view_mode': 'form',
  #           'res_model': 'unload.truck',
  #           'views': [(view_id, 'form')],
  #           'view_id': view_id,
  #           'target': 'new',
  #           'res_id': self.ids[0],
  #       }

	def unload_truck(self):
		stock_picking = self.env.context.get('active_id')
		stock_picking_id = self.env['stock.picking'].browse(stock_picking)

		if stock_picking_id:
			stock_picking_id.task_timer = False
			if self.manual_time:
				stock_picking_id.manual_time = self.manual_time
			if stock_picking_id.total_time or stock_picking_id.manual_time:
				stock_picking_id.write({
					'received_containers' : self.received_containers,
					'is_container_seal_match' : self.is_container_seal_match,
					'is_truck_container_number_match' : self.is_truck_container_number_match,
					'worker_ids' : self.worker_ids.ids,
					'state' : 'release_lorry',
					'is_unloaded':True
					})
				
				logistics_obj = self.env['logistics.management'].search([('origin' , '=' , stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')])

				stock_picking_id.load_unload_notification()

				if logistics_obj:
					for rec in logistics_obj:
						if rec.container_count == 'specified':
							if self.received_containers != stock_picking_id.no_of_container:
								stock_picking_id.write({
									'is_container_match' : True
									})
			else:
				raise UserError('Please update the loading/unloading time of truck')

		if self.container_details_line_ids:
			for line in self.container_details_line_ids:
				line.line_id.final_container_height = line.final_container_height

		return {'type': 'ir.actions.act_window_close'}


class ContainerDetailsLine(models.TransientModel):
	_name = 'container.details.line'

	container_type_id = fields.Many2one('container.type',string="Container Type")
	container_length = fields.Integer('Container Length')
	container_width = fields.Integer('Container Width')
	container_height = fields.Integer('Container Height')
	final_container_height = fields.Integer('Extra Height')
	container_count = fields.Integer('Number of Containers')
	line_id = fields.Many2one('container.type.line', string="Container Line Ref")
	container_details_line_id = fields.Many2one('unload.truck', string='Unload truck reference')