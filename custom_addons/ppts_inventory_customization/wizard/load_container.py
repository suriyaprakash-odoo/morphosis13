# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class LoadContainer(models.TransientModel):
    _name = 'load.container'

    @api.model
    def default_get(self, fields_name):
        res = super(LoadContainer, self).default_get(fields_name)
        if self._context.get('active_id'):
            stock_picking_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            product_line_list = []
            if stock_picking_id:
                if stock_picking_id.move_ids_without_package:
                    product_line_list = [(0, 0, {
                        'product_id': record.product_id.id,
                        'demand': record.product_qty,
                        'container_ids': [(6, 0, record.container_ids.ids)] if record.container_ids else [],
                        'actual_weight': record.actual_weight
                    }) for record in stock_picking_id.move_ids_without_package]

                    res.update({'container_line_ids': product_line_list})
                res.update({'truck_container_number': stock_picking_id.truck_container_number})
                res.update({'sale_logistics_no_of_container': stock_picking_id.sale_logistics_no_of_container})
                res.update({'weight_at_entry':stock_picking_id.sale_logistics_weight_at_entry,
                            'weight_at_exit':stock_picking_id.sale_logistics_weight_at_exit,
                            'actual_wt_difference':stock_picking_id.sale_logistics_weight_at_exit-stock_picking_id.sale_logistics_weight_at_entry,
                            'shipment_state':stock_picking_id.state,
                            'shipment_weight':stock_picking_id.gross_weight
                            })
        return res

    truck_container_number = fields.Char("Truck Container Number")
    sale_logistics_no_of_container = fields.Integer('Number of Container(s)')
    is_sea_transport = fields.Boolean('Is Sea Tansport')
    container_seal_number = fields.Char('Container Seal Number')
    pickup_location_id = fields.Many2one('stock.location', string='Picking Location',
                                         domain="[('usage','=','internal')]")
    container_line_ids = fields.One2many('load.container.line', 'container_line_id', string="Load Container line Ref")
    weight_at_entry = fields.Float(string="Truck weight at entry(Kg)")
    weight_at_exit = fields.Float(string="Truck weight at exit(Kg)")
    shipment_weight = fields.Float(string="Shipment Weight")
    actual_wt_difference = fields.Float(string="Actual weight")
    shipment_state = fields.Char('State')
    update_demand = fields.Boolean('Update Demand')
    # container_ids = fields.Many2many('stock.container',string="Containers")

    @api.onchange('update_demand')
    def onchange_update_demand(self):
        if self.update_demand == True:
            actual_wt = self.actual_wt_difference
            for line in self.container_line_ids:
                if line.container_ids:
                    for container in line.container_ids:
                        if container.is_vrac:
                            for fraction in container.fraction_line_ids:
                                fraction.is_to_sell = False
                            for fraction in container.fraction_line_ids:
                                if fraction.weight <= actual_wt:
                                    actual_wt = actual_wt - fraction.weight
                                    fraction.is_to_sell = True
                                    line.demand = actual_wt
                        else:
                            raise UserError(_('Please choose Vrac container'))

    def get_fractions(self):
        if self._context.get('active_id'):
            actual_wt = self.actual_wt_difference
            for line in self.container_line_ids:
                if line.container_ids:
                    for container in line.container_ids:
                        if container.is_vrac:
                            # remove existing container
                            for fraction in container.fraction_line_ids:
                                fraction.is_to_sell = False
                            for fraction in container.fraction_line_ids:
                                if fraction.weight <= actual_wt:
                                    actual_wt = actual_wt - fraction.weight
                                    fraction.is_to_sell = True
                                else:
                                    raise UserError(_('Please check the Vrac container weight.'))
                        else:
                            raise UserError(_('Please choose Vrac container'))
            if actual_wt > 0.0:
                raise UserError(_('Please enable the Update Demand to update the actual weight value or Please add the another container to update the value'))

    def load_container(self):
        stock_picking = self.env.context.get('active_id')
        stock_picking_id = self.env['stock.picking'].browse(stock_picking)
        sale_order_id = self.env['sale.order'].search([('name', '=', stock_picking_id.origin)])

        if stock_picking_id:
            stock_picking_id.write({
                'truck_container_number': self.truck_container_number,
                'sale_logistics_no_of_container': self.sale_logistics_no_of_container,
                'is_sea_transport': self.is_sea_transport,
                'container_seal_number': self.container_seal_number,
                'pickup_location_id': self.pickup_location_id,
                # 'is_unloaded': True
            })
            new_product_line = []
            for update_line in self.container_line_ids:
                for stock_line in stock_picking_id.move_ids_without_package:
                    if update_line.product_id == stock_line.product_id:
                        stock_line.container_ids = update_line.container_ids
                        stock_line.actual_weight = update_line.actual_weight

                for sale_line in sale_order_id.order_line:
                    if update_line.product_id == sale_line.product_id:
                        sale_line.container_id = update_line.container_ids
                for container in update_line.container_ids:
                    if container.is_vrac != True:
                        container.state = 'lead'

            if stock_picking_id.state == 'assigned' and stock_picking_id.incoming_truck_registered == True:
                stock_picking_id.state = 'load_unload'

            stock_picking_id.load_unload_notification()

        return {'type': 'ir.actions.act_window_close'}

class LoadContainerLine(models.TransientModel):
    _name = 'load.container.line'

    product_id = fields.Many2one('product.product', string="Product")
    container_ids = fields.Many2many('stock.container', string="Containers",
                                     domain="[('content_type_id', '=', product_id),('state','!=','sold')]")
    demand = fields.Float('Demand', digits=(12, 4))
    actual_weight = fields.Float('Actual Weight(Kg)', digits=(12, 4))
    gross_weight = fields.Float('Gross Weight(Kg)', digits=(12, 4))
    container_line_id = fields.Many2one('load.container', string="Load Containers Ref")

    @api.onchange('product_id')
    def onchage_product_id(self):
        if self.product_id:
            res = {'domain': {'container_ids': "[('id', '=', False)]"}}
            if self.product_id.container_product_ids:
                containers_list = []
                for line in self.product_id.container_product_ids:
                    containers_list.append(line.container_id.id)
                if len(containers_list) > 1:
                    if containers_list:
                        res['domain']['container_ids'] = "[('id', 'in', %s)]" % containers_list
                    else:
                        res['domain']['container_ids'] = []
                else:
                    if containers_list:
                        res['domain']['container_ids'] = "[('id', '=', %s)]" % containers_list[0]
                    else:
                        res['domain']['container_ids'] = []
            print(res)
            return res

    @api.onchange('container_ids')
    def onchange_actual_weight(self):
        if self.container_ids:
            self.actual_weight = 0.0
            for rec in self.container_ids:
                self.actual_weight += rec.net_weight
                self.gross_weight += rec.gross_weight
