# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_

class UpdateInitialDemand(models.TransientModel):
	_name = "update.initial.demand"

	@api.model
	def default_get(self, fields_name):
		res = super(UpdateInitialDemand, self).default_get(fields_name)
		print(self._context.get('active_id'))
		if self._context.get('active_id'):
			shipping_obj = self.env['stock.picking'].search([('id' , '=' , int(self._context.get('active_id')))])
			container_list = []
			for line in shipping_obj.move_ids_without_package:
				if line.container_ids:
					for container in line.container_ids:
						container_list.append(container.id)
			res.update({'container_ids': container_list})
			res.update({'picking_id': shipping_obj.id})
			res.update({'selling_weight': shipping_obj.sale_logistics_weight_at_exit - shipping_obj.sale_logistics_weight_at_entry})
		return res

	is_vrac_sale = fields.Boolean('Is VRAC Sale?')
	picking_id = fields.Many2one('stock.picking',string='Picking ID')
	selling_weight = fields.Float('Final Outgoing Weight(Kg)')
	container_ids = fields.Many2many('stock.container',string='Container')
	wizard_line_ids = fields.One2many('selling.fraction.line', 'selling_wizard_id', string='Fractions sell line ref')

	def get_fraction_list(self):
		if self.selling_weight:
			total_weight = 0.0
			remaining_weight = 0.0
			new_fraction_vals = []
			self.wizard_line_ids.unlink()
			fraction_vals = {}
			for container in self.container_ids:
				for line in container.fraction_line_ids:
					if total_weight != self.selling_weight:
						if total_weight:
							remaining_weight = self.selling_weight - total_weight
						if remaining_weight:
							if remaining_weight <= line.weight:
								new_fraction_vals.append((0, 0, {
									'fraction_id': line.fraction_id.id,
									'weight_of_fraction': remaining_weight,
									'selling_wizard_id': self.id,
									'line_id': line.id,
									}))
								line.weight = line.weight - remaining_weight
								# new_fraction_vals.append(fraction_vals)
								break
							else:
								if remaining_weight >= line.weight:
									new_fraction_vals.append((0, 0, {
										'fraction_id': line.fraction_id.id,
										'weight_of_fraction': remaining_weight - line.weight,
										'selling_wizard_id': self.id,
										'line_id': line.id,
									}))
									# new_fraction_vals.append(fraction_vals)
									total_weight += line.weight
									line.weigh = 0.0
						else:
							if self.selling_weight <= line.weight:
								new_fraction_vals.append((0, 0, {
									'fraction_id': line.fraction_id.id,
									'weight_of_fraction': self.selling_weight,
									'selling_wizard_id': self.id,
									'line_id': line.id,
									}))
								line.weight = line.weight - self.selling_weight
								# new_fraction_vals.append(fraction_vals)
								break
							else:
								fr_weight = 0.0
								if line.weight:
									if self.selling_weight > line.weight:
										fr_weight = line.weight
									else:
										fr_weight = self.selling_weight
									new_fraction_vals.append((0, 0, {
										'fraction_id': line.fraction_id.id,
										'weight_of_fraction': fr_weight,
										'selling_wizard_id': self.id,
										'line_id': line.id,
										}))
									# new_fraction_vals.append(fraction_vals)
									total_weight += line.weight
									line.weight = 0.0
			# self.env['selling.fraction.line'].create(new_fraction_vals)
		shipping_obj = self.env['stock.picking'].search([('id' , '=' , int(self._context.get('active_id')))])
		selling_weight = shipping_obj.sale_logistics_weight_at_exit - shipping_obj.sale_logistics_weight_at_entry
		container_list = []
		for line in shipping_obj.move_ids_without_package:
			if line.product_id.uom_id.name == 'Tonne':
				line.actual_weight = selling_weight / 1000
			else:
				line.actual_weight = selling_weight
			if line.container_ids:
				for container in line.container_ids:
					container_list.append(container.id)

		vals = ({
			'default_is_vrac_sale': True, 
			'default_container_ids': container_list, 
			'default_selling_weight': selling_weight,
			'default_wizard_line_ids': new_fraction_vals,
			'default_picking_id': shipping_obj.id,
			'stock_picking_id': shipping_obj.id,
			})
		print(vals,'--')
		# test
		return {
            'name': "Update Initial Demand",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.initial.demand',
            'target': 'new',
            'context': vals,
        }

	def update_initial_demand(self):
		stock_picking_id = self.env['stock.picking'].search([('id', '=', int(self._context.get('active_id')))])
		if self.is_vrac_sale:
			stock_picking_id = self.env['stock.picking'].search([('id', '=', int(self._context.get('stock_picking_id')))])
			if self.wizard_line_ids:
				weight = 0.00
				for line in self.wizard_line_ids:
					weight += line.weight_of_fraction
				for st_line in stock_picking_id.move_ids_without_package:
					st_line.actual_weight = weight
		for line in stock_picking_id.move_ids_without_package:
			if line.actual_weight:
				changed_demand = 0
				if line.product_id.uom_id.name == 'Tonne':
					changed_demand = line.actual_weight / 1000
				else:
					changed_demand = line.actual_weight

				print('line.product_uom_qty',line.product_uom_qty)

				line.product_uom_qty = 0.0
				line.product_uom_qty = changed_demand

				print(line.product_uom_qty,'line.product_uom_qty')

		sale_order_obj = self.env['sale.order'].search([('name', '=', stock_picking_id.origin)])

		if sale_order_obj:
			
			if self.wizard_line_ids:
				for line in self.wizard_line_ids:
					line.line_id.is_to_sell = True
					line.line_id.sale_order_id = sale_order_obj.id
			for line in stock_picking_id.move_ids_without_package:
				for so_line in sale_order_obj.order_line:
					if so_line.product_id == line.product_id:
						so_line.product_uom_qty = line.product_uom_qty

		stock_picking_id.action_assign()
		stock_picking_id.state = "release_lorry"

		return {'type': 'ir.actions.act_window_close'}

class SellingFractionLine(models.TransientModel):
    _name = 'selling.fraction.line'

    fraction_id = fields.Many2one('project.fraction', string='Fraction')
    weight_of_fraction = fields.Float('Weight(Kg)', digits=(12,4))
    selling_wizard_id = fields.Many2one('update.initial.demand', string='Sell partially ref')
    line_id = fields.Many2one('fraction.line', string="Fraction Line")