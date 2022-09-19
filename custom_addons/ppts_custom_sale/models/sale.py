from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime
from odoo.tools import float_is_zero, float_compare
from functools import partial
from itertools import groupby


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('logistics', 'Assign Logistics'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    no_of_container = fields.Integer('Number of Containers')
    sale_by = fields.Selection([
        ('weight', 'Weight(Kg)'),
        ('unit', 'Units'),
        ('container', 'Containers'),
        ('time', 'Time'),
        ('fixed_price', 'Fixed Price')
    ], string='Sale by')
    is_transport = fields.Boolean('Transported by us?', track_visibility='onchange')
    order_pickup_date = fields.Date('Order Pickup Date')

    transport_request_count = fields.Integer('Transport Requests', compute='compute_transport_request_count')

    transport_rfq_count = fields.Integer('RFQ Count', compute='compute_transport_rfq_count', default=0)
    hide_price = fields.Boolean("Hide Price?")

    buyer_ref = fields.Char("Buyer Reference")
    #Transport Page
    lorry_type = fields.Selection([
        ('container', 'container'),
        ('curtainside', 'Curtain-side'),
        ('semi_trailer', 'Semi-Trailer'),
        ('rigid_body_truck', 'Rigid Body Truck'),
        ('moving_floor', 'Moving Floor')
    ], string='Type of Lorry')
    pickup_location_id = fields.Many2one('res.partner', string='Pickup Location')
    # domain="['|',('parent_id' , '=?' , partner_id),('unknown_location','=',True)]"
    is_full_load = fields.Boolean('Full Load?')
    is_tail_lift = fields.Boolean('Tail-Lift')
    opening_hours_start = fields.Char('Opening Hours Start')
    opening_hours_end = fields.Char('Opening Hours End')
    morning_opening_hours_start = fields.Char('Morning Opening Hours Start')
    morning_opening_hours_end = fields.Char('Morning Opening Hours End')
    evening_opening_hours_start = fields.Char('Evening Opening Hours Start')
    evening_opening_hours_end = fields.Char('Evening Opening Hours End')
    total_quantity = fields.Float(string="Total Quantity (Kg)")
    collection_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
    ], string='Collection Date Type')
    estimated_collection_date = fields.Date('Collection Date')
    collection_date_from = fields.Date('From')
    collection_date_to = fields.Date('To')
    actual_date = fields.Date("Actual Collection Date")
    waste_code = fields.Char('Waste Code', default="16 02 16")
    tranport_mode = fields.Selection([
        ('direct', 'Direct'),
        ('route', 'Route Groupage'),
        ('air', 'Air Flight'),
        # ('sea' , 'Sea Flight'),
        ('lcl', 'Maritime Groupage(LCL)'),
        ('fcl', 'Maritime Groupage(FCL)')
    ], string='Transport Mode', default='direct')
    loading_port_id = fields.Many2one('res.sea.ports', string='Port of Loading')
    loading_port_code = fields.Char(string='Code')
    unloading_port_id = fields.Many2one('res.sea.ports', string='Port of Unloading')
    unloading_port_code = fields.Char(string='Code')
    hayons = fields.Selection([('hayons', 'Hayons'), ('hayons_t', 'Hayons + transpalette'),
                               ('hayons_te', 'Hayons + transpalette electrique')])
    container_count = fields.Selection([
        ('specified', 'Specified'),
        ('not_specified', 'Not Specified')
    ], string='Nombre de colis')
    qty_of_container = fields.Integer('Quantity of Container')
    linear_meter = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13')
    ], string="Linear Meter")

    include_logistics = fields.Boolean('Does not Include Logistics')
    shipment_validated = fields.Boolean('Shipment Validated')

    dimension = fields.Char(string="Dimension")
    material = fields.Char(string="Material")

    create_transport_request = fields.Boolean(compute="_compute_create_transport_request")

    trigger_action_confirm = fields.Boolean(compute="_compute_action_confirm")

    demand_logistics = fields.Boolean(default=False)
    action_confirm_boolean = fields.Boolean(default=False)

    is_contrack_work = fields.Boolean(string="Is Contract Work ?")

    def _compute_action_confirm(self):
        self.trigger_action_confirm = True
        if self.demand_logistics and (not self.action_confirm_boolean):
            self.action_confirm()
            self.action_confirm_boolean = True
    
    def action_draft(self):
        
        result = super(SaleOrder, self).action_draft()
        self.demand_logistics = False
        self.action_confirm_boolean = False
        return result


    def _compute_create_transport_request(self):

        self.create_transport_request = False
        if self.state=="sale":
            self.create_transport_request = True

        logistics_obj = self.env['logistics.management'].sudo().search([('sales_origin','=',self.id)])
        for logistics in logistics_obj:
            if logistics.status in ["approved","delivered"]:
                self.create_transport_request = False
                break
            

    def action_confirm_so(self):
        self.action_confirm()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'sale.order.new', sequence_date=seq_date) or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order', sequence_date=seq_date) or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result

    def _create_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                for rec in self:
                    ref_invoice_vals.update({
                        'ref': rec.buyer_ref,
                        'invoice_origin': ', '.join(origins),
                        'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                    })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Manage 'final' parameter: transform out_invoice to out_refund if negative.
        out_invoice_vals_list = []
        refund_invoice_vals_list = []
        if final:
            for invoice_vals in invoice_vals_list:
                if sum(l[2]['quantity'] * l[2]['price_unit'] for l in invoice_vals['invoice_line_ids']) < 0:
                    for l in invoice_vals['invoice_line_ids']:
                        l[2]['quantity'] = -l[2]['quantity']
                    invoice_vals['type'] = 'out_refund'
                    refund_invoice_vals_list.append(invoice_vals)
                else:
                    out_invoice_vals_list.append(invoice_vals)
        else:
            out_invoice_vals_list = invoice_vals_list

        # Create invoices.
        moves = self.env['account.move'].with_context(default_type='out_invoice').create(out_invoice_vals_list)
        moves += self.env['account.move'].with_context(default_type='out_refund').create(refund_invoice_vals_list)
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        

        # update container to done for contract work
        for order in self:
            if order.is_contrack_work:
                stock_picking = self.env['stock.picking'].sudo().search([('origin','=',order.name),('state','=','done')])

                if stock_picking:
                    for picking in stock_picking:
                        for line in picking.move_ids_without_package:
                            for container in line.container_ids:
                                container.state = "done"
        return moves

    def compute_transport_rfq_count(self):
        for rec in self:
            transport_rfq_obj = self.env['purchase.order'].search([('origin', '=', rec.name)])
            if transport_rfq_obj:
                rec.transport_rfq_count = len(transport_rfq_obj)
            else:
                rec.transport_rfq_count = 0

    def action_view_transport_rfq(self):

        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('origin', '=', self[0].name)],
            'views_id': False,
            'views': [(self.env.ref('purchase.purchase_order_tree').id or False, 'tree'),
                      (self.env.ref('purchase.purchase_order_form').id or False, 'form')],
        }

    def compute_transport_request_count(self):
        transport_obj = self.env['logistics.management'].search([('sales_origin', '=', self.id)])

        self.transport_request_count = len(transport_obj)
    

    def action_alert_logistics_sale(self):
        self.ensure_one()

        ctx = dict(self.env.context or {})

        total_weight = 0.00
        for line in self.order_line:
            if line.product_id.uom_id.name == 'Tonne' or line.product_id.uom_id.name == 'tonne':
                total_weight += line.product_uom_qty * 1000
            elif line.product_id.uom_id.name == 'Units' or line.product_id.uom_id.name == 'Unités':
                total_weight += line.product_uom_qty / 1000
            else:
                total_weight += line.product_uom_qty

        ctx.update({
            'default_pickup_partner_id': self.pickup_location_id.id if self.pickup_location_id else self.company_id.partner_id.id,
            'default_delivery_partner_id': self.partner_shipping_id.id if self.partner_shipping_id else False,
            'default_container_count': self.container_count,
            'default_linear_meter': self.linear_meter,
            'default_no_of_container': self.no_of_container,
            'default_collection_date_type':self.collection_date_type,
            'default_lorry_type': self.lorry_type,
            'default_pickup_date': self.estimated_collection_date,
            'default_pickup_earliest_date': self.collection_date_from,
            'default_pickup_latest_date': self.collection_date_to,
            'default_gross_weight': total_weight,
            'default_waste_code': self.waste_code,
            'default_dimension': self.dimension,
            'default_material': self.material,
            'default_is_full_load': self.is_full_load,
            'default_is_tail_lift': self.is_tail_lift,
            'default_hayons': self.hayons,
        })

        return {
            'name': ('Transport Notification'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'transport.popup.sale',
            'target': 'new',
            'context':ctx,
        }


    def action_move_to_logisctics(self):
        if self.sale_by == 'container':
            non_container_lines = 0
            for rec in self.order_line:
                if not rec.container_id:
                    non_container_lines = non_container_lines + 1
            
            # get stock picking details

            get_stock = self.env['stock.picking'].sudo().search([('sale_id','=',self.id)],limit=1)

            sum_qty = 0
            stock_reference = ""
            scheduled_date = ""
            if get_stock:
                stock_reference = get_stock.name
                scheduled_date = get_stock.scheduled_date
                # get sum quantity
                for move in get_stock.move_ids_without_package:
                    sum_qty += move.product_uom_qty


            if non_container_lines == 0:
                self.ensure_one()
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference('ppts_custom_sale', 'email_template_demand_for_logistics')[1]
                except ValueError:
                    template_id = False
                try:
                    compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
                except ValueError:
                    compose_form_id = False
                ctx = dict(self.env.context or {})

                ctx.update({
                    'default_model': 'sale.order',
                    'active_model': 'sale.order',
                    'active_id': self.ids[0],
                    'default_res_id': self.ids[0],
                    'default_use_template': bool(template_id),
                    'default_template_id': template_id,
                    'default_composition_mode': 'comment',
                    'custom_layout': "mail.mail_notification_paynow",
                    'default_attachment_ids': [],
                    'model_description': 'Allocate Logistics',
                    'force_email': True,
                    'mark_allocate_logistics_as_sent': True,
                    'sum_qty': sum_qty,
                    'stock_reference': stock_reference,
                    'scheduled_date': scheduled_date,
                })

                print(ctx)

                return {
                    'name': _('Compose Email'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form_id, 'form')],
                    'view_id': compose_form_id,
                    'target': 'new',
                    'context': ctx,
                }
                # self.state = 'logistics'
            else:
                raise ValidationError(_('Please Assign containers for all the line items'))
        else:
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('ppts_custom_sale', 'email_template_demand_for_logistics')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict(self.env.context or {})

            # get stock picking details

            get_stock = self.env['stock.picking'].sudo().search([('sale_id','=',self.id)],limit=1)

            sum_qty = 0
            stock_reference = ""
            scheduled_date = ""
            if get_stock:
                stock_reference = get_stock.name
                scheduled_date = get_stock.scheduled_date
                # get sum quantity
                for move in get_stock.move_ids_without_package:
                    sum_qty += move.product_uom_qty

            ctx.update({
                'default_model': 'sale.order',
                'active_model': 'sale.order',
                'active_id': self.ids[0],
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'custom_layout': "mail.mail_notification_paynow",
                'default_attachment_ids': [],
                'model_description': 'Allocate Logistics',
                'force_email': True,
                'mark_allocate_logistics_as_sent': True,
                'sum_qty': sum_qty,
                'stock_reference': stock_reference,
                'scheduled_date': scheduled_date,
            })

            print(ctx)

            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
            # self.state = 'logistics'

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_allocate_logistics_as_sent'):
            if not kwargs['partner_ids']:
                raise UserError('Please add the recipients')
            else:
                if self.env.context.get('mark_allocate_logistics_as_sent'):
                    self.write({'state': 'logistics'})
                return super(SaleOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def send_notification(self):
        ctx = dict(self.env.context or {})
        template_id = self.env.ref('ppts_custom_sale.email_template_send_notification').id
        mail_template = self.env['mail.template'].browse(template_id)

        production_mail_template_id = self.env.ref('ppts_custom_sale.email_template_send_notification_to_production').id
        production_mail_template = self.env['mail.template'].browse(production_mail_template_id)


        get_stock = self.env['stock.picking'].sudo().search([('sale_id','=',self.id)],limit=1)
        
        scheduled_date = ""
        if get_stock:
            # if not self.is_transport:
            #     get_stock.logistics_updated = True
            scheduled_date = get_stock.scheduled_date
        
        ctx.update({
            'scheduled_date': scheduled_date,
        })

        if mail_template:
            if self.sale_by == 'container':
                non_container_lines = 0
                for rec in self.order_line:
                    if not rec.container_id:
                        non_container_lines = non_container_lines + 1

                if non_container_lines == 0:
                    # self.state = 'logistics'
                    self.action_confirm()
                    mail_template.send_mail(self.id, force_send=True)
                else:
                    raise ValidationError(_('Please Assign containers for all the line items'))
            else:
                # self.state = 'logistics'
                self.action_confirm()
                mail_template.send_mail(self.id, force_send=True)

        if production_mail_template:
            production_mail_template.with_context(ctx).send_mail(self.id, force_send=True)

    def action_create_transport_request(self):
        ctx = dict()

        total_weight = 0.00
        weight_uom_id = 0
        for line in self.order_line:
            
            if line.product_id.uom_id.name == 'Tonne' or line.product_id.uom_id.name == 'tonne':
                total_weight += line.product_uom_qty * 1000
            elif line.product_id.uom_id.name == 'Units' or line.product_id.uom_id.name == 'Unités':
                total_weight += line.product_uom_qty / 1000
            else:
                total_weight += line.product_uom_qty

            weight_uom_id = line.product_uom.id

        ctx = ({
            'default_pickup_partner_id': self.pickup_location_id.id if self.pickup_location_id else self.company_id.partner_id.id,
            'default_delivery_partner_id': self.partner_shipping_id.id,
            'default_delivery_partner_location_id': self.partner_shipping_id.id,
            'default_pickup_country_id': self.pickup_location_id.country_id.id if self.pickup_location_id else self.company_id.partner_id.country_id.id,
            'default_delivery_country_id': self.partner_id.country_id.id,
            'default_company_id': self.company_id.id,
            'default_sales_origin': self.id,
            'default_no_of_container': self.no_of_container,
            'default_gross_weight': self.total_quantity,
            'default_weight_uom_id': weight_uom_id,
            'default_logistics_for': 'sale',
            'default_buyer_ref': self.buyer_ref,
            'default_status': 'new',
            'default_pickup_date_type': self.collection_date_type,
            'default_material': self.material,
            'default_container_count': self.container_count,
            'default_waste_code': self.waste_code,
            'default_pickup_date': self.estimated_collection_date,
            'default_pickup_earliest_date':self.collection_date_from,
            'default_pickup_latest_date': self.collection_date_to,
            'default_morning_opening_hours_start': self.morning_opening_hours_start,
            'default_morning_opening_hours_end': self.morning_opening_hours_end,
            'default_evening_opening_hours_start': self.evening_opening_hours_start,
            'default_evening_opening_hours_start': self.evening_opening_hours_start,
            'default_lorry_type': self.lorry_type,
            'default_transport_mode': self.tranport_mode,
            'default_loading_port_id': self.loading_port_id.id if self.loading_port_id else False,
            'default_unloading_port_id': self.unloading_port_id.id if self.unloading_port_id else False,
            'default_is_full_load': self.is_full_load,
            'default_is_tail_lift': self.is_tail_lift,
            'default_dimension': self.dimension,
            'default_linear_meter': self.linear_meter,
            'default_hayons': self.hayons,
            'default_grid_rotation': self.partner_id.grid_rotation,

        })

        form_id = self.env.ref('ppts_logistics.logistics_management_form_view').id

        return {
            'name': _('Transport Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'logistics.management',
            'views_id': False,
            'views': [(form_id or False, 'form')],
            'target': 'current',
            'context': ctx,
        }

    def action_view_transport_request(self):

        return {
            'name': _('Transport Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'logistics.management',
            'domain': [('sales_origin', '=', self[0].id)],
            'views_id': False,
            'views': [(self.env.ref('ppts_logistics.logistics_management_tree_view').id or False, 'tree'),
                      (self.env.ref('ppts_logistics.logistics_management_form_view').id or False, 'form')],
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        logistics_obj = self.env['logistics.management'].search([('sales_origin', '=', self.id), ('status', '=', 'approved')])
        if logistics_obj:
            stock_picking_id = self.env['stock.picking'].search([('origin', '=', self.name)], limit=1)
            if stock_picking_id:
                stock_picking_id.write({
                    'transporter_partner_id': logistics_obj.partner_id.id if logistics_obj.partner_id else False,
                    'vendor_ref': logistics_obj.buyer_ref,
                    'gross_weight': logistics_obj.gross_weight if logistics_obj.gross_weight else 0,
                    'sale_logistics_pickup_date': logistics_obj.pickup_date if logistics_obj.pickup_date else False,
                    'sale_logistics_expected_delivery': logistics_obj.expected_delivery if logistics_obj.expected_delivery else False,
                    'sale_logistics_no_of_container': logistics_obj.no_of_container,
                    'buyer_ref': logistics_obj.buyer_ref,
                    'logistics_updated': True,
                    'include_logistics': self.include_logistics,
                })

            
        # if self.sale_by == 'container':
        stock_picking_id = self.env['stock.picking'].search([('origin', '=', self.name)], limit=1)
        if stock_picking_id:
            # if not self.is_transport:
            #     stock_picking_id.logistics_updated = True
            stock_picking_id.vendor_ref = self.buyer_ref
            for rec in self.order_line:
                move_line = self.env["stock.move"].search([('picking_id', '=', stock_picking_id.id), ('product_uom_qty', '=', rec.product_uom_qty)])
                for line in move_line:
                    line.container_ids = rec.container_id.ids
                    if self.partner_id.country_id.code=='FR':
                        line.write({'bsd_annexe': 'bsd'})
                    else:
                        line.write({'bsd_annexe' : 'annexe7'})
        return res

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        if self.lorry_type == False:
            raise ValidationError(_('Lorry Type is not Created'))
        elif self.pickup_location_id == False:
            raise ValidationError(_('PickUp Location is not Created'))
        elif self.total_quantity == False:
            raise  ValidationError(_('Total Quantity is not Created'))
        elif self.morning_opening_hours_start == False:
            raise ValidationError(_('Morning Opening Hours is not Created'))
        elif self.morning_opening_hours_end == False:
            raise ValidationError(_('Morning Ending Hour is not Created'))
        elif self.evening_opening_hours_start == False:
            raise ValidationError(_('Evening Opening Hours is not Created'))
        elif self.evening_opening_hours_end == False:
            raise ValidationError(_('Evening Ending Hour is not Created'))
        else:
            self.ensure_one()
            template_id = self._find_mail_template()
            lang = self.env.context.get('lang')
            template = self.env['mail.template'].browse(template_id)
            if template.lang:
                lang = template._render_template(template.lang, 'sale.order', self.ids[0])
            ctx = {
                'default_model': 'sale.order',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'proforma': self.env.context.get('proforma', False),
                'force_email': True,
                'model_description': self.with_context(lang=lang).type_name,
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    container_id = fields.Many2many('stock.container', string="Container")
    potential_sale_price = fields.Monetary('Potential Sales cost', compute='_compute_potential_sales_cost')
    cost_price = fields.Monetary('Cost Price', compute='_compute_cost_price')
    weight = fields.Float('Weight(Kg)')
    account_analytic_id = fields.Many2one('account.analytic.account',string='Analytic Account')

    @api.depends('container_id')
    def _compute_potential_sales_cost(self):
        for order_line in self:
            if order_line.container_id:
                sale_value = 0.0
                for container in order_line.container_id:
                    sale_value += container.potential_sales_cost
                if sale_value != 0.0:
                    order_line.update({
                        'potential_sale_price': sale_value
                    })
                else:
                    order_line.update({
                        'potential_sale_price': 0.0
                    })
            else:
                order_line.update({
                    'potential_sale_price': 0.0
                })

    @api.depends('container_id')
    def _compute_cost_price(self):
        for order_line in self:
            if order_line.container_id:
                cost_value = 0.0
                for container in order_line.container_id:
                    if container.cross_dock == True:
                        for line in container.project_id.project_entry_ids:
                            if container.content_type_id == line.product_id:
                                cost_value += container.container_cost + container.forecast_sale_price
                            else:
                                cost_value = cost_value

                        if cost_value != 0.0:
                            order_line.update({
                                'cost_price': cost_value
                            })
                        else:
                            order_line.update({
                                'cost_price': cost_value
                            })
                    else:
                        for line in container.fraction_line_ids:
                            transport = 0.0
                            if line.fraction_id.source_container_id.project_id.confirmed_transport_cost:
                                transport = line.fraction_id.source_container_id.project_id.confirmed_transport_cost / container.net_weight
                            cost_value += container.cost_per_ton + transport
                        if cost_value != 0.0:
                            order_line.update({
                                'cost_price': cost_value
                            })
                        else:
                            order_line.update({
                                'cost_price': cost_value
                            })
            else:
                order_line.update({
                    'cost_price': 0.0
                })

    @api.onchange('product_id')
    def onchange_containers(self):
        res = {'domain': {'container_id': "[('id', '=', False)]"}}
        if self.product_id:
            if self.product_id.container_product_ids:
                containers_list = []
                for line in self.product_id.container_product_ids:
                    containers_list.append(line.container_id.id)
                if containers_list:
                    res['domain']['container_id'] = "[('id', 'in', %s)]" % containers_list
                else:
                    res['domain']['container_id'] = []
        return res

    @api.onchange('container_id')
    def onchange_container_id(self):
        if self.container_id:
            weight = 0.0
            final_weight = 0.0
            for line in self.container_id:
                weight += line.net_weight
                if line.content_type_id.uom_id.uom_type == 'bigger':
                    final_weight = weight / line.content_type_id.uom_id.factor_inv
                elif line.content_type_id.uom_id.uom_type == 'smaller':
                    final_weight = weight * line.content_type_id.uom_id.factor
                else:
                    final_weight = weight
            self.product_uom_qty = final_weight

    # @api.onchange('container_id')
    # def onchange_unit_price(self):
    # 	if self.container_id:
    # 		self.price_unit = self.container_id.forecasted_sales_price
