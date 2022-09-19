# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_
from datetime import timedelta, datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class SearchChronopostProject(models.TransientModel):
	_name = 'search.chronopost.project'


	chronopost_number = fields.Char('Chronopost Number')


	def search_and_open_project(self):
		if self.chronopost_number:
			chronopost_line_obj = self.env['carton.line'].search([('name', '=', self.chronopost_number)],limit=1)
			container_obj = self.env['project.container'].search([('chronopost_number', '=', chronopost_line_obj.id)],limit=1)
			
			if container_obj:
				container_id = container_obj.id
			else:
				raise ValidationError('There is no container associated to this Chronopost Number!')
						

		# if chronopost_line_obj:
		# 	project_id = chronopost_line_obj.carton_id.id
		# else:
		# 	project_id = False

		tree_id = self.env.ref('ppts_inventory_customization.project_container_tree_view').id
		form_id = self.env.ref('ppts_inventory_customization.project_container_form_view').id

		return{
                'name': ('Source Container'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id' : container_id,
                'res_model': 'project.container',
                'views': [(form_id, 'form')],
                'view_id': False,
                'target': 'current',
                }