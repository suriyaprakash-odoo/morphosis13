# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _

class MoveToProduction(models.TransientModel):
	_name = 'move.to.production'

	operator_ids = fields.Many2many("hr.employee", string="Operator", tracking=True, domain="[('is_worker','=', True)]")

	def set_inprogress(self):
		container_id = self.env.context.get('active_id')
		container_obj = self.env['project.container'].browse(container_id)

		if container_obj:
			container_obj.write({
				'operator_ids' : self.operator_ids,
				'state' : 'in_progress',
				})
			container_obj.parent_rc_id.state = 'done'
			if container_obj.child_container_ids:
				for child_con in container_obj.child_container_ids:
					child_con.parent_rc_id.state = 'done'

		return {'type': 'ir.actions.act_window_close'}