# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_


class RegisterChronopost(models.TransientModel):
	_name = "register.chronopost"

	@api.model
	def default_get(self, fields_name):
		res = super(RegisterChronopost, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
			container_obj = self.env['project.container'].search([('picking_id' , '=' , stock_picking_id.id),('project_id' , '=' ,stock_picking_id.project_entry_id.id)])
			transport = self.env['res.partner'].search([('is_chronopost','=',True)],limit=1)
			transporter = False
			if transport:
				transporter = transport.id

			container_line_list = []
			if container_obj:
				container_line_list = [(0, 0, {
					'container_id':record.id,
					'source_location_id':record.location_id.id,
					'chronopost_number':record.chronopost_number.name or ''
					})for record in container_obj]

				res.update({'container_line_ids': container_line_list})
			res.update({'project_id' : stock_picking_id.project_entry_id.id})
			res.update({'shipment_id' : stock_picking_id.id,'logistics_partner_id':transporter})


		return res

	project_id = fields.Many2one('project.entries', domain="[('status','in', ('reception','wip'))]")
	shipment_id = fields.Many2one('stock.picking')
	logistics_partner_id = fields.Many2one('res.partner', string='Transporter', domain="[('is_chronopost', '=', True)]")
	container_line_ids = fields.One2many('chronopost.container.line','chronopost_line_id', string="Chronoport line ref")

	def register_chronopost(self):
		if self.logistics_partner_id:
			self.shipment_id.transporter_partner_id = self.logistics_partner_id.id
		if self.container_line_ids:
			for rec in self.container_line_ids:
				if rec.not_received:
					rec.container_id.not_received = rec.not_received
					rec.container_id.not_received_reason = rec.not_received_reason
					rec.container_id.have_batteries = rec.have_batteries
					rec.container_id.batteries_weight = rec.batteries_weight
					rec.container_id.state = 'close'
				else:
					rec.container_id.have_batteries = rec.have_batteries
					rec.container_id.batteries_weight = rec.batteries_weight
					rec.container_id.location_id = rec.destination_location_id


		self.shipment_id.state = 'production'

		return {'type': 'ir.actions.act_window_close'}


class ChronopostContainerLine(models.TransientModel):
	_name = "chronopost.container.line"

	container_id = fields.Many2one('project.container', string="Container")
	chronopost_number = fields.Char('Chronoport Barcode')
	source_location_id = fields.Many2one('stock.location', string='Source Location', domain="[('usage','=','internal')]")
	destination_location_id = fields.Many2one('stock.location', string='Destination Location', domain="[('usage','=','internal')]")
	not_received = fields.Boolean('Not Received')
	not_received_reason = fields.Char('Reason')
	have_batteries = fields.Boolean('Batteries')
	batteries_weight = fields.Float('Batteries Weight', digits=(12,4))
	chronopost_line_id = fields.Many2one('register.chronopost', string='Chronoport ref')


	@api.onchange('container_id')
	def onchange_container_id(self):
		if self.container_id:
			self.source_location_id = self.container_id.location_id.id
			self.chronopost = self.container_id.chronopost_number