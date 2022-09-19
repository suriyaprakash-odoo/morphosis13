# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api,_
from datetime import timedelta, datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class TransportRfq(models.TransientModel):
	_name = 'transport.rfq'

	@api.model
	def default_get(self, fields_name):
		res = super(TransportRfq, self).default_get(fields_name)
		if self._context.get('partner_id'):
			res.update({'partner_id': self._context.get('partner_id')})

		return res

	partner_id = fields.Many2one('res.partner',string = 'Customer', domain="[('is_transporter', '=', True)]")
	product_id = fields.Many2one('product.product',string = "Product",domain="[('type', '=', 'service')]")
	currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
	quoted_price = fields.Monetary('Quoted Price', currency_field='currency_id')

	add_cost_existing_po = fields.Boolean(string="Include Cost in PO?",default=False)

	def create_transport_po(self):
		logistics = self.env.context.get('active_id')
		logistics_id = self.env['logistics.management'].browse(logistics)

		if self.quoted_price == 0.00:
			raise ValidationError('Please enter the Quoted Price for logistics.')

		project_id = False
		if logistics_id.logistics_for == 'sale':
			origin = logistics_id.sales_origin.name
			if logistics_id.company_id != logistics_id.sales_origin.company_id:
				raise ValidationError('The company in sale order and logistics is different.')
		if logistics_id.logistics_for == 'purchase':
			origin = logistics_id.origin.origin.name
			project_id = logistics_id.origin.id
			if logistics_id.company_id != logistics_id.origin.company_id:
				raise ValidationError('The company in Project entry and logistics is different.')

		line_vals = []
		line_vals.append((0, 0, {
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_qty': 1,
            'price_unit': self.quoted_price,
            'product_uom': self.product_id.uom_id.id,
            'date_planned':datetime.now().date()
            }))

		create_po_obj = self.env['purchase.order'].create({
			'partner_id' : self.partner_id.id,
			'company_id' : logistics_id.company_id.id,
			'order_line' : line_vals,
			'origin' : origin,
			'is_transport_rfq' : True,
			'logistics_id' : logistics_id.id,
			'project_entry_id':project_id
			})

		if create_po_obj:

			logistics_id.write({
					'purchase_order_id' : create_po_obj.id,
					'transport_cost' : self.quoted_price,
					'status' : 'approved'
				})

			if logistics_id.logistics_for == 'purchase':
				if not logistics_id.origin.is_registered_package:
					logistics_id.origin.confirmed_transport_cost = self.quoted_price
				if logistics_id.name == 'New':
					seq_date = None
					if logistics_id.create_date:
						seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(logistics_id.create_date))
					logistics_id.name = logistics_id.origin.name + '/' + self.env['ir.sequence'].next_by_code('logistics.management', sequence_date=seq_date) or '/'

				template_id = self.env.ref('ppts_logistics.email_template_send_approved_notification').id
				mail_template = self.env['mail.template'].browse(template_id)

				if mail_template:
					logistics_id.origin.status = 'in_transit'
					mail_template.send_mail(logistics_id.id, force_send=True)
				
				if self.add_cost_existing_po:
					logistics_id.origin.origin.order_line = line_vals
					
				# logistics_id.origin.origin.button_confirm()
				transport_obj = self.env['logistics.management'].search([('origin' , '=' , logistics_id.origin.id),('id' , '!=' , logistics_id.id)])
				if transport_obj:
					for rec in transport_obj:
						rec.status = 'rejected'
						rec.active = False
				
				# update transport details in shipment
				shipment_obj = self.env['stock.picking'].sudo().search([('origin','=',logistics_id.origin.origin.name)])

				if shipment_obj:

					shipment_transport_data = {
						'sale_logistics_pickup_date': logistics_id.pickup_date,
						'sale_logistics_expected_delivery': logistics_id.expected_delivery,
						'sale_logistics_no_of_container': logistics_id.no_of_container,
						'gross_weight': logistics_id.gross_weight,
						'logistics_updated': True,
						'transporter_partner_id': logistics_id.partner_id.id if logistics_id.partner_id else False,
					}

					for picking in shipment_obj:
						picking.update(shipment_transport_data)

			if logistics_id.logistics_for == 'sale':
				if logistics_id.name == 'New':
					seq_date = None
					if logistics_id.create_date:
						seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(logistics_id.create_date))

					logistics_id.name = logistics_id.sales_origin.name + '/' + self.env['ir.sequence'].next_by_code('logistics.management', sequence_date=seq_date) or '/'
				
				if logistics_id.sales_origin.state!="sale":
					logistics_id.sales_origin.action_confirm()

				template_id = self.env.ref('ppts_logistics.email_template_send_approved_notification_to_production').id
				mail_template = self.env['mail.template'].browse(template_id)

				if mail_template:
					mail_template.send_mail(logistics_id.id, force_send=True)

				transport_obj = self.env['logistics.management'].search([('sales_origin' , '=' , logistics_id.sales_origin.id),('id' , '!=' , logistics_id.id)])

				if transport_obj:
					for rec in transport_obj:
						rec.status = 'rejected'
						rec.active = False
				
				# update transport details in sale order
				sale_transport_data = {
					'pickup_location_id': logistics_id.pickup_partner_id.id if logistics_id.pickup_partner_id else False,
					'no_of_container': logistics_id.no_of_container,
					'total_quantity': logistics_id.gross_weight,
					'buyer_ref': logistics_id.buyer_ref,
					'collection_date_type': logistics_id.pickup_date_type,
					'container_count': logistics_id.container_count,
					'material': logistics_id.material,
					'waste_code': logistics_id.waste_code,
					'estimated_collection_date': logistics_id.pickup_date,
					'collection_date_from': logistics_id.pickup_earliest_date,
					'collection_date_to': logistics_id.pickup_latest_date,
					'morning_opening_hours_start': logistics_id.morning_opening_hours_start,
					'morning_opening_hours_end': logistics_id.morning_opening_hours_end,
					'evening_opening_hours_start': logistics_id.evening_opening_hours_start,
					'evening_opening_hours_start': logistics_id.evening_opening_hours_start,
					'lorry_type': logistics_id.lorry_type,
					'tranport_mode': logistics_id.tranport_mode,
					'loading_port_id': logistics_id.loading_port_id.id if logistics_id.loading_port_id else False,
					'unloading_port_id': logistics_id.unloading_port_id.id if logistics_id.unloading_port_id else False,
					'is_full_load': logistics_id.is_full_load,
					'is_tail_lift': logistics_id.is_tail_lift,
				}

				sales_origin.update(sale_transport_data)

				# update transport details in shipment
				shipment_transport_data = {
					'sale_logistics_pickup_date': logistics_id.pickup_date,
					'sale_logistics_expected_delivery': logistics_id.expected_delivery,
					'sale_logistics_no_of_container': logistics_id.no_of_container,
					'gross_weight': logistics_id.gross_weight,
					'logistics_updated': True,
					'transporter_partner_id': logistics_id.partner_id.id if logistics_id.partner_id else False,
				}
				
				picking_ids = self.env['stock.picking'].search([('origin' , '=' , sales_origin.name)])
				for picking in picking_ids:
					picking.update(shipment_transport_data)

			start_date = datetime.strptime(str(logistics_id.expected_delivery)+" 00:00:00", '%Y-%m-%d %H:%M:%S')
			duration = 1
			if logistics_id.expected_delivery_start_time and logistics_id.expected_delivery_end_time:

				stime = logistics_id.expected_delivery_start_time

				hours = int(stime)
				minutes = (stime*60) % 60
				# seconds = (stime*3600) % 60

				start_time = "%d:%02d" % (hours, minutes)

				start_date = str(logistics_id.expected_delivery)+ " "+start_time
				start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M')

				etime = logistics_id.expected_delivery_end_time

				hours = int(etime)
				minutes = (etime*60) % 60
				# seconds = (etime*3600) % 60

				end_time = "%d:%02d" % (hours, minutes)

				end_date = str(logistics_id.expected_delivery)+ " "+end_time
				end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
				
				FMT = '%Y-%m-%d %H:%M'
				tdelta = end_date - start_date

				duration = abs(tdelta.total_seconds()/3600)


			x = datetime.strptime(str(start_date), '%Y-%m-%d %H:%M:%S')
			stop_date = x + timedelta(hours=duration)

			updated_name = None
			if logistics_id:
				load_status = None
				if logistics_id.is_full_load == True:
					load_status = 'Full Load'+','
				else:
					load_status = str(logistics_id.no_of_container)+','
				updated_name = logistics_id.name+'['+str(logistics_id.partner_id.name)+','+str(logistics_id.vendor_ref)+','+load_status+str(logistics_id.pickup_state_id.name)+']'
			else:
				updated_name=logistics_id.name

			calender_obj = self.env['calendar.event'].create({
					'name' : logistics_id.name,
				'updated_name' : updated_name,
					'start' : start_date,
					'stop' : stop_date,
					'duration' : duration,
					'state' : 'draft',
					'logistics_id' : logistics_id.id,
					'logistics_partner_id' : logistics_id.partner_id.id,
					'logistics_pickup_partner_id' : logistics_id.pickup_partner_id.id,
					'logistics_delivery_partner_id' : logistics_id.delivery_partner_id.id,
					'pickup_state_id' : logistics_id.pickup_state_id.id,
					'delivery_state_id' : logistics_id.delivery_state_id.id,
					'gross_weight' : logistics_id.gross_weight,
					'pickup_date_type' : logistics_id.pickup_date_type,
					'pickup_date' : logistics_id.pickup_date or '',
					'pickup_earliest_date' : logistics_id.pickup_earliest_date or '',
					'pickup_latest_date' : logistics_id.pickup_latest_date or '',
					'expected_delivery' : logistics_id.expected_delivery or '',
					'logistics_calendar' : True
				})
				
			create_po_obj.button_confirm()

		return {'type': 'ir.actions.act_window_close'}

