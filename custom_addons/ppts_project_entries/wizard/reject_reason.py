# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_


class RejectProjectEntry(models.TransientModel):
	_name = 'reject.project.entry'

	name = fields.Char('Reject Reason')

	def reject_project_entry(self):
		project_obj = self.env.context.get('active_id')
		project_id = self.env['project.entries'].browse(project_obj)

		if project_id:
			project_id.is_offer_reject = True
			project_id.reject_reason = self.name
			project_id.status = 'reject'

		return {'type': 'ir.actions.act_window_close'}

