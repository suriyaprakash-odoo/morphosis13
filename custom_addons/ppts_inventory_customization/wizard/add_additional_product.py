# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_


class AddAdditionalProduct(models.TransientModel):
	_name = "add.additional.product"

	@api.model
	def default_get(self, fields_name):
		res = super(AddAdditionalProduct, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
			res.update({'shipment_id' : stock_picking_id.id})

		return res

	shipment_id = fields.Many2one('stock.picking')
	additional_product_line_ids = fields.One2many('additional.product.line','additional_product_line_id', string="Additional Product line ref")


	def action_add_additional_product(self):
		if self.additional_product_line_ids:
			so_obj = self.env['sale.order'].search([('name','=',self.shipment_id.origin)])
			shipment_line_list = []
			so_line_list = []
			for line in self.additional_product_line_ids:
				shipment_line_list.append((0, 0, {
						'product_id':line.product_id.id,
						'name':line.product_id.name,
						'container_ids':line.container_ids.ids,
						'product_uom_qty':line.product_qty,
						'product_uom':line.product_uom_id.id,
						'location_id':self.shipment_id.location_id.id,
						'location_dest_id':self.shipment_id.location_id.id,
					}))
				so_line_list.append((0,0, {
						'product_id':line.product_id.id,
						'container_id':line.container_ids.ids,
						'name':line.product_id.name,
						'product_uom_qty':line.product_qty,
						'product_uom':line.product_uom_id.id,
						'price_unit':line.product_id.lst_price
					}))
			self.shipment_id.move_ids_without_package = shipment_line_list
			self.shipment_id.state = 'load_unload'
			so_obj.order_line = so_line_list
		return {'type': 'ir.actions.act_window_close'}


class AdditionalProductLine(models.TransientModel):
	_name = "additional.product.line"

	additional_product_line_id = fields.Many2one('add.additional.product', string='Add Additional Product Ref')
	product_id = fields.Many2one('product.product', domain="[('type', 'in', ['product', 'consu'])]", string='Product')
	container_ids = fields.Many2many('stock.container',string='Container',domain="[('content_type_id', '=', product_id),('state','!=','sold')]")
	product_qty = fields.Float('Quantity')
	product_uom_id = fields.Many2one('uom.uom', 'UoM')

	@api.onchange('product_id')
	def onchage_product_id(self):
		if self.product_id:
			self.product_uom_id = self.product_id.uom_id.id

	@api.onchange('container_ids')
	def onchange_product_qty(self):
		if self.container_ids:
			self.product_qty = 0.0
			for rec in self.container_ids:
				if self.product_uom_id.name == 'Tonne' or self.product_uom_id.name == 'Units' or self.product_uom_id.name == 'Unités':
					self.product_qty += rec.net_weight/1000
				else:
					self.product_qty += rec.net_weight