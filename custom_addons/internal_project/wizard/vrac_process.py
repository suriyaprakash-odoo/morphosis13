# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_

class CompleteVrac(models.TransientModel):
	_name = 'complete.vrac'

	@api.model
	def default_get(self, fields_name):
		res = super(CompleteVrac, self).default_get(fields_name)
		print(self._context.get('active_id'))
		if self._context.get('active_id'):
			internal_project_obj = self.env['internal.project'].search([('id' , '=' , int(self._context.get('active_id')))])
			res.update({'internal_project_id': internal_project_obj.id})
			for rec in internal_project_obj.container_ids:
				product_id = rec.content_type_id.id
			res.update({'product_id': product_id})
		return res

	internal_project_id = fields.Many2one('internal.project', string='Internal Project')
	product_id = fields.Many2one('product.product', string='Product')
	recipient_container_id = fields.Many2one("stock.container", "Destination Container", domain="[('is_vrac', '!=', False)]")
	operator_id = fields.Many2one("hr.employee", "Operator",domain="[('is_worker','=', True)]")

	def action_complete_vrac_process(self):
		if self.internal_project_id.action_type == 'vrac':
			product_templete_obj = self.env['product.template'].browse(int(self.product_id.product_tmpl_id))
			fraction_id = self.env["project.fraction"].create({
				'internal_project_id': self.internal_project_id.id,
				'worker_id' : self.operator_id.id,
				'is_vrac' : True,
				'second_process' : True,
				'main_product_id': product_templete_obj.id,
				'sub_product_id': self.product_id.id,
				'recipient_container_id':self.recipient_container_id.id,
				'fraction_by':'weight',
				'container_weight':self.internal_project_id.net_weight,
				'fraction_weight': self.internal_project_id.net_weight,
				'company_id': self.env.user.company_id.id,
				})

			fraction_id.close_fraction()
			for rec in self.internal_project_id.container_ids:
				rec.state = 'done'
				rec.is_internal_project_closed = True
			self.internal_project_id.state = 'done'
			return {
                'name': _('Fraction'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.fraction',
                'res_id': fraction_id.id,
                'view_id': False,
                'target': 'current',
            }