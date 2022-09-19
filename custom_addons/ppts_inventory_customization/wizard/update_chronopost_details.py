# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_
import math
from odoo.exceptions import Warning

class UpdateChronopostDetails(models.TransientModel):
	_name = 'update.chronopost'

	project_id = fields.Many2one('project.entries', string="Project Entry", domain="[('status','in', ('reception','wip'))]")
	update_chronopost_line_ids = fields.One2many('update.chronopost.line','update_chronopost_line_id', string='Chronopost line ref')

	@api.onchange('project_id')
	def onchange_project_id(self):
		if self.project_id:
			container_obj = self.env['project.container'].search([('project_id' , '=' , self.project_id.id)])
			if container_obj:
				container_line_list = [(0, 0, {
					'container_id':record.id,
					'chronopost_number':record.chronopost_number,
					'sur_charges':record.chronopost_number.sur_charges,
					'gross_weight':record.gross_weight,
					})for record in container_obj]

			self.update_chronopost_line_ids = container_line_list
			self.project_id.update_transport_cost()

	def update_chronopost(self):
		if self.update_chronopost_line_ids:
			for rec in self.update_chronopost_line_ids:
				if math.ceil(rec.gross_weight) <= 0:
					raise Warning("Gross Weight should not be negative/zero")

				rec.container_id.chronopost_number = rec.chronopost_number
				rec.container_id.gross_weight = rec.gross_weight
				rec.chronopost_number.sur_charges = rec.sur_charges

				chronopost_obj = self.env['carton.line'].sudo().search([('name','=',rec.chronopost_number.name)])
				for i in chronopost_obj:
					i.sur_charges = rec.sur_charges

		return {'type': 'ir.actions.act_window_close'}


class UpdateChronopostLine(models.TransientModel):
	_name = 'update.chronopost.line'

	container_id = fields.Many2one('project.container', string="Container")
	project_id = fields.Many2one(comodel_name='project.entries', related="container_id.project_id")
	chronopost_number = fields.Many2one(comodel_name="carton.line", domain="[('carton_id','=',project_id)]")
	sur_charges = fields.Float('Sur Charges(%)')
	gross_weight = fields.Float("Gross Weight")
	update_chronopost_line_id = fields.Many2one('update.chronopost', 'Update Chronopost Ref')

	
	@api.onchange("chronopost_number")
	def _onchange_chronopost_number(self):
		if self.chronopost_number:
			self.sur_charges = self.chronopost_number.sur_charges
		


	# @api.onchange('container_id')
	# def onchage_container_id(self):
	# 	res={'domain':{'chronopost_number': "[('id', '=', False)]"}}
	# 	if self.container_id:
	# 		chronopost_list = []
	# 		chronopost_obj = self.env['carton.line'].search([('carton_id' , '=' , self.container_id.project_id.id)])
	# 		for line in chronopost_obj:
	# 			chronopost_list.append(line.id)
	# 		if len(chronopost_list) > 1:
	# 			if chronopost_list:
	# 				res['domain']['chronopost_number'] = "[('id', 'in', %s)]" % chronopost_list
	# 			else:
	# 				res['domain']['chronopost_number'] = []
	# 		else:

	# 			if chronopost_list:
	# 				res['domain']['chronopost_number'] = "[('id', '=', %s)]" % chronopost_list[0]
	# 			else:
	# 				res['domain']['chronopost_number'] = []
