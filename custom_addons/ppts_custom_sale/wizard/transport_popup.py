from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class TransportPopupSale(models.TransientModel):
    _name = 'transport.popup.sale'
    _description = 'Transport Popup for sales'

    pickup_partner_id = fields.Many2one('res.partner',string="Pickup Point")
    delivery_partner_id = fields.Many2one('res.partner',string="Delivery Point")

    collection_date_type = fields.Selection([
        ('specific', 'Specific Date'),
        ('between', 'In between'),
        ('as_soon_as_possible', 'As soon as possible')
    ], string='Pickup Date Type')

    gross_weight = fields.Float("Gross Weight")
    waste_code = fields.Char("Waste Code")
    material = fields.Char("Material")

    container_count = fields.Selection([
        ('specified', 'Specified'),
        ('not_specified', 'Not Specified')
    ], string='Nombre de colis')

    no_of_container = fields.Integer("Container Count")

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

    dimension = fields.Char("Dimension")

    lorry_type = fields.Selection([
        ('container', 'container'),
        ('curtainside', 'Curtain-side'),
        ('semi_trailer', 'Semi-Trailer'),
        ('rigid_body_truck', 'Rigid Body Truck'),
        ('moving_floor', 'Moving Floor')
    ], string='Type of Lorry')

    pickup_date = fields.Date("Pickup Date")
    pickup_earliest_date = fields.Date("Earliest Date")
    pickup_latest_date = fields.Date('Latest Date')

    is_full_load = fields.Boolean('Full Load?')
    is_tail_lift = fields.Boolean('Tail-Lift')
    hayons = fields.Selection([('hayons', 'Hayons'), ('hayons_t', 'Hayons + transpalette'),
                               ('hayons_te', 'Hayons + transpalette electrique')])

    note = fields.Text("Note")


    def send_transport_notificaton(self):

        if not self.pickup_partner_id:
            raise UserError('Please select Pickup Point')
        sale_id = self.env["sale.order"].browse(self.env.context.get('active_id'))
        vals = {
            'pickup_location_id': self.pickup_partner_id.id,
            'partner_shipping_id': self.delivery_partner_id.id,
            'collection_date_type': self.collection_date_type,
            'estimated_collection_date': self.pickup_date,
            'collection_date_from': self.pickup_earliest_date,
            'collection_date_to': self.pickup_latest_date,
            'total_quantity': self.gross_weight,
            'waste_code': self.waste_code,
            'material': self.material,
            'container_count': self.container_count,
            'qty_of_container': self.no_of_container,
            'no_of_container': self.no_of_container,
            'linear_meter': self.linear_meter,
            'dimension': self.dimension,
            'lorry_type': self.lorry_type,
            'note': self.note,
            'is_full_load': self.is_full_load,
            'is_tail_lift': self.is_tail_lift,
            'hayons': self.hayons,
            'demand_logistics': True,
            'action_confirm_boolean': False,
        }
        sale_id.update(vals)
        
        template_id = self.env.ref('ppts_custom_sale.email_template_demand_for_logistics').id
        mail_template = self.env['mail.template'].browse(template_id)

        if mail_template:
            if sale_id.sale_by == 'container':
                non_container_lines = 0
                for rec in sale_id.order_line:
                    if not rec.container_id:
                        non_container_lines = non_container_lines + 1
                
                # get stock picking details

                get_stock = self.env['stock.picking'].sudo().search([('sale_id','=',sale_id.id)],limit=1)

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
                    ctx = dict(self.env.context or {})

                    ctx.update({
                        'mark_allocate_logistics_as_sent': True,
                        'sum_qty': sum_qty,
                        'stock_reference': stock_reference,
                        'scheduled_date': scheduled_date,
                    })

                    mail_template.with_context(ctx).send_mail(sale_id.id, force_send=True)
                else:
                    raise ValidationError(_('Please Assign containers for all the line items'))
            
            else:
                self.ensure_one()
                ctx = dict(self.env.context or {})

                # get stock picking details

                get_stock = self.env['stock.picking'].sudo().search([('sale_id','=',sale_id.id)],limit=1)

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
                    'mark_allocate_logistics_as_sent': True,
                    'sum_qty': sum_qty,
                    'stock_reference': stock_reference,
                    'scheduled_date': scheduled_date,
                })

                mail_template.with_context(ctx).send_mail(sale_id.id, force_send=True)
        








    
