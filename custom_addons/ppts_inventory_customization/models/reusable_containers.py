from odoo import fields, models, api, _
from datetime import timedelta, datetime
from odoo.exceptions import ValidationError

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    reuse_barcode = fields.Char("Barcode")

    @api.model
    def create(self, vals):
        res = super(StockQuant, self).create(vals)
        if res.lot_id:
            res.reuse_barcode = res.lot_id.reuse_barcode
        return res


class ReuseContainers(models.Model):
    _name = 'reusable.containers'

    name = fields.Char("Sequence")
    state = fields.Selection([('draft', 'Draft'), ('client', 'Client'),('production','Production'), ('stock', 'Stock')], string="State", tracking=True, default='draft')
    partner_id = fields.Many2one("res.partner", string="Client")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    shipment_date = fields.Date("Shipment Date")
    # reuse_line = fields.One2many("reuse.container.line", "reuse_id", string="Containers")
    container_status_line = fields.One2many("container.status", "status_id", string="Status")


class ReuseContainersLine(models.Model):
    _name = 'reuse.container.line'

    product_id = fields.Many2one("product.product", string="Container")
    quantity = fields.Float("Quantity")
    # reuse_id = fields.Many2one("reusable.containers")
    logistics_id = fields.Many2one("logistics.management")


class ReuseContainersStatus(models.Model):
    _name = 'container.status'

    product_id = fields.Many2one("product.product", string="Container")
    quantity = fields.Float("Quantity")
    lot_id = fields.Many2one("stock.production.lot", string="LOT/Serial")
    return_date = fields.Date("Return Date")
    status_id = fields.Many2one("reusable.containers")
    picking_id = fields.Many2one("stock.picking", string="Return Shipment")
    # delivery_id = fields.Many2one("stock.picking", string="Delivery Order")
    state = fields.Selection([('client', 'With Client'), ('Production', 'In Production'), ('stock', 'Stock')], string="State", tracking=True)


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    for_container = fields.Boolean("Container Operation")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    reuse_id = fields.Many2one("reusable.containers", "Reuse ID")
    transport_id = fields.Many2one("logistics.management", string="Transport ID")



class Logistics(models.Model):
    _inherit = 'logistics.management'

    send_containers = fields.Boolean("Send Containers")
    # reuse_container_id = fields.Many2one('reusable.containers', string="Reuse Containers")
    container_line_ids = fields.One2many('logistics.container.line', 'logistics_id', string="Containers")
    transport_type = fields.Selection(selection_add=[('drop_off', 'Collection Drop off')])


    def action_view_shipment(self):
        shipment_id = False
        if self.send_containers:
            shipment_id = self.env['stock.picking'].search([('transport_id', '=', self.id)])
        else:
            if self.logistics_for == 'purchase':
                print(self.origin.origin.name)
                shipment_id = self.env['stock.picking'].search([('project_entry_id', '=', self.origin.id)])
            else:
                shipment_id = self.env['stock.picking'].search([('origin', '=', self.sales_origin.name)])

        return {
            'name': _('Shipment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', shipment_id.ids)],
            'views_id': False,
            'views': [(self.env.ref('stock.vpicktree').id or False, 'tree'),
                      (self.env.ref('stock.view_picking_form').id, 'form')],
        }


class LogisticsContainers(models.Model):
    _name = 'logistics.container.line'

    product_id = fields.Many2one("product.product", string="Container", domain="[('product_tmpl_id.reuse_container','=',True)]")
    quantity = fields.Float("Quantity")
    logistics_id = fields.Many2one("logistics.management")


class TransportRfq(models.TransientModel):
    _inherit = 'transport.rfq'


    def create_transport_po(self):
        logistics = self.env.context.get('active_id')
        logistics_id = self.env['logistics.management'].browse(logistics)
        if self.quoted_price == 0.00:
            raise ValidationError('Please enter the Quoted Price for logistics.')

        if logistics_id.send_containers:
            list_items = []
            picking_type = self.env["stock.picking.type"].search([('for_container', '=', True), ('company_id', '=', logistics_id.company_id.id)], limit=1)
            if not picking_type:
                raise ValidationError('Operation type is not created for Re-use container process, '
                                      'Please create a operation type for re-use container process with "Container Operation" check box enabled!')
            for line in logistics_id.container_line_ids:
                list_items.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'location_dest_id': self.partner_id.property_stock_customer.id,
                }))

            transport_po_obj = self.env['purchase.order'].search([('origin', '=', logistics_id.origin.origin.name)])

            picking_id = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                # 'scheduled_date': logistics_id.reuse_container_id.shipment_date,
                'move_type': 'direct',
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': logistics_id.delivery_partner_id.property_stock_customer.id,
                'partner_id': logistics_id.partner_id.id,
                'move_ids_without_package': list_items,
                'company_id': logistics_id.company_id.id or False,
                'transport_id': logistics_id.id,

                'project_entry_id':logistics_id.origin.id or False,
                'transporter_partner_id':logistics_id.partner_id.id or False,
                'gross_weight': logistics_id.gross_weight or '',
                'pickup_date_type': logistics_id.pickup_date_type,
                'pickup_date': logistics_id.pickup_date,
                'pickup_earliest_date': logistics_id.pickup_earliest_date,
                'pickup_latest_date': logistics_id.pickup_latest_date,
                'expected_delivery': logistics_id.expected_delivery,
                'no_of_container': logistics_id.no_of_container or '',
                'user_id': False,
                'date': transport_po_obj.date_order,
                'origin': transport_po_obj.name,
                'logistics_updated': True,
                'transport_po_id': transport_po_obj.id

            })
            print(picking_id,'========================')
        origin = ''
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
            'date_planned': datetime.now().date()
        }))

        create_po_obj = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'company_id': logistics_id.company_id.id,
            'order_line': line_vals,
            'origin': origin,
            'is_transport_rfq': True,
            'logistics_id': logistics_id.id,
            'project_entry_id': project_id,
            'is_internal_purchase': True
        })

        if create_po_obj:

            logistics_id.write({
                'purchase_order_id': create_po_obj.id,
                'transport_cost': self.quoted_price,
                'status': 'approved'
            })

            if logistics_id.logistics_for == 'purchase':
                if not logistics_id.origin.is_registered_package:
                    logistics_id.origin.confirmed_transport_cost = self.quoted_price
                # logistics_id.origin.confirmed_transport_cost = self.quoted_price
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

                print("line_vals===",line_vals)
                if self.add_cost_existing_po:
                    logistics_id.origin.origin.order_line = line_vals

                # logistics_id.origin.origin.button_confirm()
                # updating shipment
                if logistics_id.origin.origin.state!="purchase":
                    logistics_id.origin.origin.button_confirm()

                po_name = logistics_id.origin.origin.name
                get_shipment = self.env['stock.picking'].sudo().search([('origin','=',po_name)],limit=1)

                if get_shipment:

                    get_shipment.update({
                        'transporter_partner_id':logistics_id.partner_id.id or '',
                        'gross_weight':logistics_id.gross_weight or '',
                        # 'weight_uom_id':logistics_id.weight_uom_id.id or '',
                        'pickup_date_type':logistics_id.pickup_date_type,
                        'pickup_date':logistics_id.pickup_date,
                        'pickup_earliest_date':logistics_id.pickup_earliest_date,
                        'pickup_latest_date':logistics_id.pickup_latest_date,
                        'expected_delivery':logistics_id.expected_delivery,
                        'no_of_container':logistics_id.no_of_container or '',
                    })
                transport_obj = self.env['logistics.management'].search([('origin', '=', logistics_id.origin.id), ('id', '!=', logistics_id.id)])
                if transport_obj:
                    for rec in transport_obj:
                        rec.status = 'rejected'
                        rec.active = False

            if logistics_id.logistics_for == 'sale':
                if logistics_id.name == 'New':
                    seq_date = None
                    if logistics_id.create_date:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(logistics_id.create_date))

                    logistics_id.name = logistics_id.sales_origin.name + '/' + self.env['ir.sequence'].next_by_code('logistics.management', sequence_date=seq_date) or '/'

                logistics_id.sales_origin.action_confirm()

                template_id = self.env.ref('ppts_logistics.email_template_send_approved_notification_to_production').id
                mail_template = self.env['mail.template'].browse(template_id)

                if mail_template:
                    mail_template.send_mail(logistics_id.id, force_send=True)

                transport_obj = self.env['logistics.management'].search([('sales_origin', '=', logistics_id.sales_origin.id), ('id', '!=', logistics_id.id)])

                if transport_obj:
                    for rec in transport_obj:
                        rec.status = 'rejected'
                        rec.active = False
            
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

            calender_obj = self.env['calendar.event'].create({
                    'name' : logistics_id.name,
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
                    'pickup_date' : logistics_id.pickup_date,
                    'pickup_earliest_date' : logistics_id.pickup_earliest_date,
                    'pickup_latest_date' : logistics_id.pickup_latest_date,
                    'expected_delivery' : logistics_id.expected_delivery,
                    'logistics_calendar' : True
                })

            create_po_obj.button_confirm()

        return {'type': 'ir.actions.act_window_close'}
