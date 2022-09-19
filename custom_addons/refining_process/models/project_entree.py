from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

class ProjectEntree(models.Model):
    _inherit = 'project.entries'

    refining_containers = fields.One2many("refining.containers","project_id", string="Refining Containers")


    def action_create_transport_request(self):
        ctx = dict()

        for rec in self:
            carton_line_list = [(0, 0, {
                'name': record.name,
                'cost': record.cost
            }) for record in rec.carton_ids]


        containers=[]
        transport_type = ''
        if self.send_containers:
            transport_type = 'drop_off'
            if self.project_container_ids:
                for ct in self.project_container_ids:
                    containers.append((0, 0, {
                        'product_id': ct.product_id.id,
                        'quantity': ct.quantity,
                    }))
            else:
                raise UserError(_('Please add some containers to send'))

        rf_containers = []
        is_refining = False
        if self.project_type == 'refine' and  self.refining_containers:
            is_refining = True
            for rct in self.refining_containers:
                rf_containers.append((0, 0, {
                    'product_id': rct.product_id.id,
                    'container_type_id': rct.container_type_id.id,
                    'gross_weight': rct.gross_weight,
                    'tare_weight': rct.tare_weight,
                    'net_weight': rct.net_weight,
                    'adr_id': rct.adr_id.id,
                    'un_id': rct.un_id.id,
                    'seal_number': rct.seal_number,
                    'name': self.name
                }))


        total_weight = 0.00
        weight_uom_id = 0
        for line in self.project_entry_ids:
            # if line.product_uom.name == 'Tonne':
            #     total_weight += (line.product_qty * 1000)
            # else:
            #     total_weight += line.product_qty
            
            if line.product_id.uom_id.uom_type == 'bigger':
                total_weight += line.product_qty * line.product_id.uom_id.factor_inv
            elif line.product_id.uom_id.uom_type == 'smaller':
                total_weight += line.product_qty / line.product_id.uom_id.factor
            else:
                total_weight += line.product_qty

            weight_uom_id = line.product_uom.id

        ctx = ({
            'default_pickup_partner_id': self.partner_id.id,
            'default_delivery_partner_id': self.company_id.partner_id.id,
            'default_pickup_country_id': self.partner_id.state_id.id,
            'default_delivery_country_id': self.company_id.partner_id.state_id.id,
            'default_company_id': self.company_id.id,
            'default_origin': self.id,
            'default_no_of_container': round(self.no_of_container),
            'default_lorry_type': self.lorry_type,
            'default_is_tail_lift': self.is_tail_lift,
            'default_morning_opening_hours_start': self.morning_opening_hours_start,
            'default_morning_opening_hours_end': self.morning_opening_hours_end,
            'default_evening_opening_hours_start': self.evening_opening_hours_start,
            'default_evening_opening_hours_end': self.evening_opening_hours_end,
            'default_pickup_date_type': self.collection_date_type,
            'default_pickup_date': self.estimated_collection_date,
            'default_pickup_earliest_date': self.collection_date_from,
            'default_pickup_latest_date': self.collection_date_to,
            'default_is_full_load': self.is_full_load,
            'default_gross_weight': total_weight,
            'default_weight_uom_id': weight_uom_id,
            'default_carton_ids': carton_line_list,
            'default_pickup_street': self.street,
            'default_pickup_street2': self.street2,
            'default_pickup_zip': self.zip,
            'default_carton_pickup_city': self.city,
            'default_state_id': self.state_id,
            'default_pickup_countries_id': self.country_id,
            'default_logistics_for': 'purchase',
            'default_status': 'new',
            'default_send_containers': self.send_containers,
            'default_container_line_ids': containers,
            'default_transport_type': transport_type,
            'default_is_refining':is_refining,
            'default_refining_containers': rf_containers

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


class RefiningContainers(models.Model):
    _name = 'refining.containers'
    
    refining_sample_id = fields.Many2one('project.refining.sample', string='Refining Sample')
    container_type_id = fields.Many2one("container.type", string="Container Type")
    product_id = fields.Many2one("product.product", string="Product")
    gross_weight = fields.Float("Gross Weight(kg)")
    tare_weight = fields.Float("Tare Weight(kg)")
    net_weight = fields.Float("Net Weight(kg)", compute='_compute_net_weight')
    adr_id = fields.Many2one("adr.class", string="ADR")
    un_id = fields.Many2one("un.code", string="UN Code")
    seal_number = fields.Char("Seal Number")
    project_id = fields.Many2one("project.entries")
    name = fields.Char("ID")
    move_dest_ids = fields.One2many('stock.move', 'created_purchase_line_id', 'Downstream Moves')
    propagate_date = fields.Boolean(string="Propagate Rescheduling", help='The rescheduling is propagated to the next move.')
    propagate_date_minimum_delta = fields.Integer(string='Reschedule if Higher Than', help='The change must be higher than this value to be propagated')
    propagate_cancel = fields.Boolean('Propagate cancellation', default=True)
    order_id = fields.Many2one('purchase.order', string='Purchase Order', related="project_id.origin")
    date_planned = fields.Datetime(string='Receipt Date', default=fields.Datetime.now)
    price_unit = fields.Float('Unit Price', related='product_id.lst_price')
    product_uom = fields.Many2one('uom.uom', 'Product UOM', related='product_id.uom_id')
    product_qty = fields.Float('Quantity', related='net_weight')
    product_uom_qty = fields.Float('Quantity', related='net_weight')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('refining.container.seq') or '/'
        return super(RefiningContainers, self).create(vals)

    @api.onchange('container_type_id')
    def onchange_container_type_id(self):
        if self.container_type_id:
            self.tare_weight = self.container_type_id.tare_weight

    @api.depends('gross_weight', 'tare_weight')
    def _compute_net_weight(self):
        for container in self:
            container.update({
                'net_weight':  container.gross_weight - container.tare_weight
            })


    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id, partner=line.order_id.partner_id
            )['total_void']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(), round=False)
        return price_unit

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_order,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'description_picking': self.product_id._get_description(self.order_id.picking_type_id),
            'propagate_cancel': self.propagate_cancel,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': self.net_weight,
            'product_uom': self.product_id.uom_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            po_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(diff_quantity, quant_uom)
            template['product_uom_qty'] = product_uom_qty
            template['product_uom'] = product_uom.id
        res.append(template)
        return res

    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)
        return self.env['stock.move'].create(values)


    

