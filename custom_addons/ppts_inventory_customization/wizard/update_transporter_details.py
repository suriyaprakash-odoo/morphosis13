from odoo import fields, models, api, _
from odoo.exceptions import UserError


class UpdateTransporterDetails(models.TransientModel):
    _name = 'update.transporter.details'

    partner_id = fields.Many2one('res.partner', string='Transporter', domain="[('is_transporter', '=', True)]")
    gross_weight = fields.Float('Gross Weight(Kg)', digits=(12,4))
    date_of_pickup = fields.Date('Picking Date')
    expected_delivery = fields.Date('Expected Delivery')
    no_of_containers = fields.Integer('Number of Containers')

    expected_delivery_start_time = fields.Float('Time Duration')
    expected_delivery_end_time = fields.Float('Time Duration')

    def update_transport_details(self):
        stock_picking = self.env.context.get('active_id')
        stock_picking_id = self.env['stock.picking'].browse(stock_picking)

        if stock_picking_id.picking_type_id.sequence_code == 'IN':
            stock_picking_id.write({'transporter_partner_id': self.partner_id, 'gross_weight': self.gross_weight, 'pickup_date': self.date_of_pickup, 'expected_delivery': self.expected_delivery, 'no_of_container': self.no_of_containers,'logistics_updated':True})
            logistics_obj = self.env['logistics.management'].search([('origin', '=', stock_picking_id.project_entry_id.id)],limit=1)
            if logistics_obj:
                logistics_obj.partner_id = self.partner_id.id
                logistics_obj.gross_weight = self.gross_weight
                logistics_obj.expected_delivery_start_time = self.expected_delivery_start_time
                logistics_obj.expected_delivery_end_time = self.expected_delivery_end_time
                
            # self.env['logistics.management'].create({
            #     'partner_id': self.partner_id.id,
            #     'company_id': stock_picking_id.company_id.id,
            #     'pickup_partner_id': stock_picking_id.partner_id.id,
            #     'pickup_street': stock_picking_id.project_entry_id.pickup_location_id.street,
            #     'pickup_street2': stock_picking_id.project_entry_id.pickup_location_id.street2,
            #     'pickup_zip': stock_picking_id.project_entry_id.pickup_location_id.zip,
            #     'pickup_city': stock_picking_id.project_entry_id.pickup_location_id.city,
            #     'pickup_state_id': stock_picking_id.project_entry_id.pickup_location_id.state_id.id,
            #     'pickup_countries_id': stock_picking_id.project_entry_id.pickup_location_id.country_id.id,
            #     'gross_weight': self.gross_weight,
            #     'logistics_for': 'purchase',
            #     'origin': stock_picking_id.project_entry_id.id,
            #     'delivery_partner_id': stock_picking_id.project_entry_id.company_id.partner_id.id,
            #     'delivery_street': stock_picking_id.project_entry_id.company_id.partner_id.street,
            #     'delivery_street2': stock_picking_id.project_entry_id.company_id.partner_id.street2,
            #     'delivery_zip': stock_picking_id.project_entry_id.company_id.partner_id.zip,
            #     'delivery_city': stock_picking_id.project_entry_id.company_id.partner_id.city,
            #     'delivery_state_id': stock_picking_id.project_entry_id.company_id.partner_id.state_id.id,
            #     'delivery_countries_id': stock_picking_id.project_entry_id.company_id.partner_id.country_id.id,
            #     'pickup_date_type': 'specific',
            #     'pickup_date': self.date_of_pickup,
            #     'expected_delivery': self.expected_delivery,
            #     'container_count': 'specified',
            #     'no_of_container': self.no_of_containers,
            #     'status' : 'approved'
            # })

        if stock_picking_id.picking_type_id.sequence_code == 'OUT':
            stock_picking_id.write({'transporter_partner_id': self.partner_id, 'gross_weight': self.gross_weight, 'sale_logistics_pickup_date': self.date_of_pickup, 'sale_logistics_expected_delivery': self.expected_delivery, 'sale_logistics_no_of_container': self.no_of_containers,'logistics_updated':True})
            sale_order_obj = self.env['sale.order'].search([('name' , '=' , stock_picking_id.origin)])
            self.env['logistics.management'].create({
                'partner_id': self.partner_id.id,
                'company_id': stock_picking_id.company_id.id,
                'pickup_partner_id': stock_picking_id.company_id.partner_id.id,
                'pickup_street': stock_picking_id.company_id.partner_id.street,
                'pickup_street2': stock_picking_id.company_id.partner_id.street2,
                'pickup_zip': stock_picking_id.company_id.partner_id.zip,
                'pickup_city': stock_picking_id.company_id.partner_id.city,
                'pickup_state_id': stock_picking_id.company_id.partner_id.state_id.id,
                'pickup_countries_id': stock_picking_id.company_id.partner_id.country_id.id,
                'gross_weight': self.gross_weight,
                'logistics_for': 'sale',
                'sales_origin': sale_order_obj.id,
                'delivery_partner_id': stock_picking_id.partner_id.id,
                'delivery_street': stock_picking_id.partner_id.street,
                'delivery_street2': stock_picking_id.partner_id.street2,
                'delivery_zip': stock_picking_id.partner_id.zip,
                'delivery_city': stock_picking_id.partner_id.city,
                'delivery_state_id': stock_picking_id.partner_id.state_id.id,
                'delivery_countries_id': stock_picking_id.partner_id.country_id.id,
                'pickup_date': self.date_of_pickup,
                'expected_delivery': self.expected_delivery,
                'expected_delivery_start_time': self.expected_delivery_start_time,
                'expected_delivery_end_time': self.expected_delivery_end_time,
                'container_count': 'specified',
                'no_of_container': self.no_of_containers,
                'status' : 'approved'
            })
