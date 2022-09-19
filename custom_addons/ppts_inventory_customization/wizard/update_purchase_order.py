# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_
from collections import OrderedDict
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class UpdatePurchaseOrder(models.TransientModel):
	_name = "update.purchase.order"

	@api.model
	def default_get(self, fields_name):
		res = super(UpdatePurchaseOrder, self).default_get(fields_name)
		if self._context.get('active_id'):
			stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
			purchase_id = self.env['purchase.order'].search([('name', '=', stock_picking_id.origin)])
			container_obj = self.env['project.container'].search([('picking_id' , '=' , stock_picking_id.id),('project_id' , '=' ,stock_picking_id.project_entry_id.id),('is_child_container', '=', False)])
			recipient_obj = self.env['stock.container'].search([('project_id' , '=' ,stock_picking_id.project_entry_id.id),('picking_id' , '=' , stock_picking_id.id)])
			vrac_fraction_obj = self.env['project.fraction'].search([('project_id', '=', stock_picking_id.project_entry_id.id),('is_vrac', '=', True)])
			product_list = []
			fraction_po_line_list = []
			for dc in container_obj:
				fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', dc.id)])
				for fraction in fraction_obj:
					if fraction.sub_product_id.id not in product_list:
						product_list.append(fraction.sub_product_id.id)
			for rc in recipient_obj:
				if rc.content_type_id.id not in product_list:
					product_list.append(rc.content_type_id.id)
			for vrac_fraction in vrac_fraction_obj:
				if vrac_fraction.sub_product_id.id not in product_list:
					product_list.append(vrac_fraction.sub_product_id.id)

			for product_id in product_list:
				quantity = 0.0
				final_qty = 0.0
				fraction_unit_weight = 0.0
				product_obj = self.env['product.product'].browse(int(product_id))
				for donor_container in container_obj:
					dc_fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', donor_container.id),('sub_product_id', '=', product_id)])
					for fraction in dc_fraction_obj:
						if fraction.fraction_by == 'weight':
							quantity += fraction.fraction_weight
						else:
							quantity += fraction.number_of_pieces
							fraction_unit_weight += fraction.fraction_weight
				rc_obj = self.env['stock.container'].search([('project_id' , '=' ,stock_picking_id.project_entry_id.id),('picking_id' , '=' , stock_picking_id.id),('cross_dock', '=', True),('content_type_id', '=', product_id)])
				for rec_con in rc_obj:
					quantity += rec_con.net_weight
				fr_obj = self.env['project.fraction'].search([('project_id', '=', stock_picking_id.project_entry_id.id),('is_vrac', '=', True),('sub_product_id', '=', product_id)])
				for vrac_fr in fr_obj:
					if vrac_fr.fraction_by == 'weight':
						quantity += vrac_fr.fraction_weight
					else:
						quantity += vrac_fr.number_of_pieces
						fraction_unit_weight += vrac_fr.fraction_weight

				if product_obj.uom_id.name == 'Tonne' or product_obj.uom_id.name == 'tonne':
					final_qty = quantity / 1000
				# elif product_obj.uom_id.name == 'kg':
				# 	final_qty = quantity * 1000
				else:
					final_qty = quantity
				

				product_price = product_obj.ecologic_price if stock_picking_id.project_entry_id.is_ecologic else product_obj.lst_price

				if stock_picking_id.project_entry_id.is_ecologic:
					calculated_offer = product_price
				else:
					if stock_picking_id.project_entry_id.margin_class == 'class_a':
						calculated_offer = ((product_price) *(1 - (stock_picking_id.project_entry_id.company_id.sale_margin_a / 100)))
					elif stock_picking_id.project_entry_id.margin_class == 'class_b':
						calculated_offer = ((product_price) *(1 - (stock_picking_id.project_entry_id.company_id.sale_margin_b / 100)))
					else:
						calculated_offer = ((product_price) *(1 - (stock_picking_id.project_entry_id.company_id.sale_margin_c / 100)))

				fraction_po_line_list.append((0, 0, {
						'product_id' : product_obj.id,
						'po_qty' : final_qty,
						'fraction_unit_weight' : fraction_unit_weight,
						'po_qty_uom' : product_obj.uom_id.id,
						'price_unit' : product_price,
						'calculated_offer_price' : calculated_offer,
						'shipment_id' : stock_picking_id.id,
					}))

			# product_line_list = []
			# product_list_dup = []
			# po_product_list_dup = []
			# non_po_line_list = []
			# final_product_list = []
			# if purchase_id.order_line:
			# 	for record in purchase_id.order_line:
			# 		po_product_list_dup.append(record.product_id.id)
			# 		container_qty = 0.0
			# 		rc_qty = 0.0
			# 		for container in container_obj:
			# 			fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', container.id)])
			# 			if not fraction_obj:
			# 				product_list_dup.append(container.sub_product_id.id)
			# 				if record.product_id == container.sub_product_id:
			# 					container_qty += container.net_gross_weight
			# 			else:
			# 				for fraction in fraction_obj:
			# 					product_list_dup.append(fraction.sub_product_id.id)
			# 					if record.product_id == fraction.sub_product_id:
			# 						if fraction.fraction_by == 'weight':
			# 							container_qty += fraction.fraction_weight
			# 						else:
			# 							container_qty += fraction.number_of_pieces

			# 		if rc_obj:
			# 			for rc in rc_obj:
			# 				product_list_dup.append(rc.content_type_id.id)
			# 				if record.product_id == rc.content_type_id:
			# 					rc_qty += rc.net_weight	
								
			# 		product_line_list.append((0, 0, {
			# 							'line_id':record.id,
			# 							'product_id':record.product_id.id,
			# 							'po_qty':record.product_qty,
			# 							'po_qty_uom':record.product_uom.id,
			# 							'container_qty':container_qty + rc_qty
			# 							}))
			# 	res.update({'product_line_ids': product_line_list})

			# container_product_list = list(OrderedDict.fromkeys(product_list_dup))
			# po_product_list = list(OrderedDict.fromkeys(po_product_list_dup))

			# common = list(set.intersection(set(po_product_list),set(container_product_list)))

			# po_product_list.extend(container_product_list)
			# final_product_list = [i for i in po_product_list if i not in common]

			# # non_po_product_list = list(OrderedDict.fromkeys(non_po_product_list_dup))
			# for product_id in final_product_list:
			# 	print(product_id,'-product_id-')
			# 	product_obj = self.env['product.product'].browse(int(product_id))
			# 	print(product_obj.name,'----')
			# 	dc_obj = self.env['project.container'].search([('picking_id' , '=' , stock_picking_id.id),('project_id' , '=' ,stock_picking_id.project_entry_id.id)])
			# 	rec_con_obj = self.env['stock.container'].search([('project_id' , '=' ,stock_picking_id.project_entry_id.id),('picking_id' , '=' , stock_picking_id.id),('content_type_id', '=', int(product_id))])
			# 	print(dc_obj)
			# 	qty = final_qty = 0.0
			# 	if dc_obj:
			# 		for dc in dc_obj:
			# 			dc_fraction_obj = self.env['project.fraction'].search([('source_container_id', '=', dc.id)])
			# 			if not dc_fraction_obj:
			# 				qty += dc.gross_weight
			# 			else:
			# 				for fraction in dc_fraction_obj:
			# 					if product_obj == fraction.sub_product_id:
			# 						if fraction.fraction_by == 'weight':
			# 							qty += fraction.fraction_weight
			# 						else:
			# 							qty += fraction.number_of_pieces

			# 	if rec_con_obj:
			# 		for rc in rec_con_obj:
			# 			qty += rc.gross_weight
				
			# 	if product_obj.uom_id.name == 'Tonne':
			# 		final_qty = (qty / 1000)
			# 	else:
			# 		final_qty = qty

			# 	if stock_picking_id.project_entry_id.margin_class == 'class_a':
			# 		calculated_offer = ((product_obj.lst_price) *(1 - (stock_picking_id.project_entry_id.company_id.sale_margin_a / 100)))
			# 	elif stock_picking_id.project_entry_id.margin_class == 'class_b':
			# 		calculated_offer = ((product_obj.lst_price) *(1 - (stock_picking_id.project_entry_id.company_id.sale_margin_b / 100)))
			# 	else:
			# 		calculated_offer = ((product_obj.lst_price) *(1 - (stock_picking_id.project_entry_id.company_id.sale_margin_c / 100)))
			# 	non_po_line_list.append((0, 0, {
			# 			'product_id' : product_obj.id,
			# 			'po_qty' : final_qty,
			# 			'po_qty_uom' : product_obj.uom_id.id,
			# 			'price_unit' : product_obj.lst_price,
			# 			'calculated_offer_price' : calculated_offer
			# 		}))
			# res.update({'non_po_line_ids' : non_po_line_list})
			res.update({'non_po_line_ids' : fraction_po_line_list})
			res.update({'shipment_id' : stock_picking_id.id})
			res.update({'purchase_id' : purchase_id.id})

		return res

	shipment_id = fields.Many2one('stock.picking', string="Shipment ID")
	purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
	product_line_ids = fields.One2many('update.purchase.order.line','product_line_id', string="Product line ref")
	non_po_line_ids = fields.One2many('non.purchase.order.line','non_po_line_id', string="Non PO line ref")

	def update_po(self):
		if self.purchase_id:
			po_line_list = []
			if self.purchase_id.order_line:				
				po_line_list = [(0, 0, {
							'product_id':record.product_id.id,
							'description':record.name,
							'product_qty':record.product_qty,
							'product_uom':record.product_uom.id,
							'price_unit':record.price_unit,
							'price_subtotal':record.price_subtotal
							})for record in self.purchase_id.order_line]

			revision_obj = self.env['purchase.revision.history'].create({
					'po_number' : self.purchase_id.name,
					'partner_id' : self.purchase_id.partner_id.id,
					'purchase_revision_id' : self.purchase_id.id,
					'revision_product_line_ids' : po_line_list
				})

			x = self.purchase_id.name.split("-")

			po_revision_name = x[0] + '-' + self.purchase_id.next_revision_number

			next_po_revision_number = int(self.purchase_id.next_revision_number) + 1

			self.purchase_id.name = po_revision_name
			self.purchase_id.next_revision_number = str(0) + str(next_po_revision_number)
			self.shipment_id.origin = po_revision_name

		# if self.product_line_ids:
		# 	for line in self.product_line_ids:
		# 		if line.product_id.uom_id.name == 'Tonne':
		# 			line.line_id.product_qty = (line.container_qty / 1000)
		# 		else:
		# 			line.line_id.product_qty = line.container_qty

		fraction_po_line_list = []
		update_quantity = 0.0
		update_weight_qty = 0.0
		final_update_qty = 0.0
		if self.non_po_line_ids:
			for line in self.non_po_line_ids:
				if line.offer_price != 0.00:
					update_quantity += line.po_qty
					if line.product_id.fraction_by_count != True:
						if line.product_id.uom_id.name == 'kg':
							update_weight_qty += (line.po_qty/1000)
						else:
							update_weight_qty += line.po_qty
					fraction_po_line_list.append((0, 0, {
											'product_id':line.product_id.id,
											'description':str(line.product_id.name) + ' - ' + str(line.product_id.product_template_attribute_value_ids.name),
											'product_qty':line.po_qty,
											'price_unit': line.offer_price,
							                'product_uom': line.po_qty_uom.id,
							                #'date_planned': datetime.now(),
										}))
				else:
					raise UserError('Please update offer price!')


			self.purchase_id.mask_po_line_ids = fraction_po_line_list

		project_update_line = []
		for update_line in self.non_po_line_ids:
			for project_line in self.shipment_id.project_entry_id.project_entry_ids:
				if update_line.product_id == project_line.product_id:
					project_line.product_qty = update_line.po_qty
					project_line.offer_price = line.offer_price
				else:
					project_update_line.append((0, 0, {
						'product_id':update_line.product_id.id,
						'name':update_line.product_id.name,
		                'product_uom': update_line.product_id.uom_id.id,
						'product_qty':update_line.po_qty,
						'price_unit':update_line.price_unit,
						'offer_price': update_line.offer_price,
		                'margin_class':self.shipment_id.project_entry_id.margin_class,
		                'project_entry_id':self.shipment_id.project_entry_id.id,
					}))
		self.shipment_id.project_entry_id.project_entry_ids = project_update_line

		for po_line in self.shipment_id.project_entry_id.origin.order_line:
			if po_line.product_id.type != 'service':
				if po_line.product_id.fraction_by_count:
					po_line.product_qty = update_quantity
				else:
					fraction_piece_weight = 0.0
					final_update_qty = 0.0
					for non_po_line in self.non_po_line_ids:
						if non_po_line.product_id.uom_id.name == 'kg':
							fraction_piece_weight += non_po_line.fraction_unit_weight/1000
						else:
							fraction_piece_weight += non_po_line.fraction_unit_weight
					if po_line.product_id.uom_id.name == 'Tonne' or po_line.product_id.uom_id.name == 'tonne':
						final_update_qty = fraction_piece_weight/1000
					# elif po_line.product_id.uom_id.name == 'kg':
					# 	final_update_qty = fraction_unit_weight / 1000
					else:
						final_update_qty = fraction_piece_weight

					print(final_update_qty,'--final_update_qty--')
					print(update_weight_qty,'--update_weight_qty--')
					po_line.product_qty = final_update_qty + update_weight_qty

		if self.shipment_id.state != 'done':
			self.shipment_id.state = 'sorted_treated'
		else:
			self.shipment_id.state = 'done'

		return {'type': 'ir.actions.act_window_close'}


class UpdatePurchaseOrderLine(models.TransientModel):
	_name = "update.purchase.order.line"

	line_id = fields.Many2one('purchase.order.line', string='Product Line ID')
	product_id = fields.Many2one('product.product', string='Product')
	po_qty = fields.Float('Quantity in PO', digits=(12,4))
	po_qty_uom = fields.Many2one('uom.uom', string='Unit of Measure')
	container_qty = fields.Float('Quantity based on containers(kg)', digits=(12,4))
	product_line_id = fields.Many2one('update.purchase.order', string='Update PO ref')


class NonPurchaseOrderLine(models.TransientModel):
	_name = "non.purchase.order.line"

	product_id = fields.Many2one('product.product', string='Product')
	po_qty = fields.Float('Quantity', digits=(12,4))
	fraction_unit_weight = fields.Float('Fraction Unit Weight', digits=(12,4))
	po_qty_uom = fields.Many2one('uom.uom', string='Unit of Measure')
	price_unit = fields.Float('Unit Price')
	calculated_offer_price = fields.Float('Calculated Offer Price')
	offer_price = fields.Float('Final Offer Price')
	shipment_id = fields.Many2one('stock.picking', string="Shipment ID")
	non_po_line_id = fields.Many2one('update.purchase.order', string='Update PO ref')

	@api.onchange('price_unit')
	def onchange_price_unit(self):

		product_price = self.product_id.ecologic_price if self.shipment_id.project_entry_id.is_ecologic else self.product_id.lst_price

		if self.shipment_id.project_entry_id.is_ecologic:
			calculated_offer = product_price
		else:
			if self.shipment_id.project_entry_id.margin_class == 'class_a':
				calculated_offer = ((product_price) *(1 - (self.shipment_id.project_entry_id.company_id.sale_margin_a / 100)))
			elif self.shipment_id.project_entry_id.margin_class == 'class_b':
				calculated_offer = ((product_price) *(1 - (self.shipment_id.project_entry_id.company_id.sale_margin_b / 100)))
			else:
				calculated_offer = ((product_price) *(1 - (self.shipment_id.project_entry_id.company_id.sale_margin_c / 100)))

		self.calculated_offer_price = calculated_offer