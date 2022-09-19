# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ReleaseTruck(models.TransientModel):
    _name = 'release.truck'

    @api.model
    def default_get(self, fields_name):
        res = super(ReleaseTruck, self).default_get(fields_name)
        print(self._context.get('active_id'))
        if self._context.get('active_id'):
            shipping_obj = self.env['stock.picking'].search([('id', '=', int(self._context.get('active_id')))])
            res.update({'sale_logistics_weight_at_entry': shipping_obj.sale_logistics_weight_at_entry})
            res.update({'sale_logistics_weight_at_exit': shipping_obj.sale_logistics_weight_at_exit})
            res.update({'sale_logistics_exit_date_time': shipping_obj.sale_logistics_exit_date_time})
            if shipping_obj.move_ids_without_package:
                res.update({'bsd_annexe': shipping_obj.move_ids_without_package[0].bsd_annexe})
            if shipping_obj.move_line_ids_without_package:
                res.update({'bsd_annexe': shipping_obj.move_ids_without_package[0].bsd_annexe})

        return res

    sale_logistics_weight_at_entry = fields.Float('Truck Weight at entry(Kg)', digits=(12, 4))
    sale_logistics_weight_at_exit = fields.Float('Truck weight at exit(Kg)', digits=(12, 4))
    sale_logistics_exit_date_time = fields.Datetime('Truck exit time', default=fields.Datetime.now)
    bsd_annexe = fields.Selection([
        ('bsd', 'BSD'),
        ('annexe7', 'Annexe7')
    ], string='BSD/Annexe7')

    def print_bsd_report(self):
        stock_picking = self.env.context.get('active_id')
        stock_picking_id = self.env['stock.picking'].browse(stock_picking)
        if stock_picking_id.picking_type_id.sequence_code == 'IN':
            logistics_obj = self.env['logistics.management'].search([('origin' , '=' , stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')],limit=1)
            return self.env.ref('ppts_logistics.report_bsd').report_action(logistics_obj)

        if stock_picking_id.picking_type_id.sequence_code == 'OUT':
            sales_obj = self.env['sale.order'].search([('name' , '=' , stock_picking_id.origin)])
            logistics_obj = self.env['logistics.management'].search([('sales_origin' , '=' , sales_obj.id),('status' , '=' , 'approved')],limit=1)
            return self.env.ref('ppts_logistics.report_bsd').report_action(logistics_obj)

    def print_annux_report(self):
        stock_picking = self.env.context.get('active_id')
        stock_picking_id = self.env['stock.picking'].browse(stock_picking)
        if stock_picking_id.picking_type_id.sequence_code == 'IN':
            logistics_obj = self.env['logistics.management'].search([('origin' , '=' , stock_picking_id.project_entry_id.id),('status' , '=' , 'approved')],limit=1)
            return self.env.ref('ppts_logistics.report_annux').report_action(logistics_obj)

        if stock_picking_id.picking_type_id.sequence_code == 'OUT':
            sales_obj = self.env['sale.order'].search([('name' , '=' , self.picking_id.origin)])
            logistics_obj = self.env['logistics.management'].search([('sales_origin' , '=' , sales_obj.id),('status' , '=' , 'approved')],limit=1)
            return self.env.ref('ppts_logistics.report_annux').report_action(logistics_obj)

    def release_truck(self):
        stock_picking = self.env.context.get('active_id')
        stock_picking_id = self.env['stock.picking'].browse(stock_picking)
        if stock_picking_id:
            stock_picking_id.write({
                'sale_logistics_weight_at_exit': self.sale_logistics_weight_at_exit,
                'sale_logistics_exit_date_time': self.sale_logistics_exit_date_time,
                'state': 'sorted_treated'
            })
            sale_obj = self.env['sale.order'].search([('name', '=', stock_picking_id.origin)])
            if sale_obj:
                logistics_obj = self.env['logistics.management'].search(
                    [('sales_origin', '=', sale_obj.id), ('status', '=', 'approved')])
                if logistics_obj:
                    logistics_obj.status = 'delivered'
        # if stock_picking_id and stock_picking_id.move_line_ids_without_package:
        #     for move_line in stock_picking_id.move_line_ids_without_package:
        #         move_line.update({'bsd_annexe': self.bsd_annexe})
        return {'type': 'ir.actions.act_window_close'}


class UpdateOutgoingTruckWeight(models.TransientModel):
    _name = 'update.outgoing.weight'

    @api.model
    def default_get(self, fields_name):
        res = super(UpdateOutgoingTruckWeight, self).default_get(fields_name)
        print(self._context.get('active_id'))
        if self._context.get('active_id'):
            shipping_obj = self.env['stock.picking'].search([('id', '=', int(self._context.get('active_id')))])
            res.update({'sale_logistics_weight_at_entry': shipping_obj.sale_logistics_weight_at_entry})

        return res

    sale_logistics_weight_at_entry = fields.Float('Truck Weight at entry(Kg)', digits=(12, 4))
    sale_logistics_weight_at_exit = fields.Float('Truck weight at exit(Kg)', digits=(12, 4))
    sale_logistics_exit_date_time = fields.Datetime('Truck exit time', default=fields.Datetime.now)

    def update_weight(self):
        stock_picking = self.env.context.get('active_id')
        stock_picking_id = self.env['stock.picking'].browse(stock_picking)
        if stock_picking_id:
            stock_picking_id.write({
                'sale_logistics_weight_at_exit': self.sale_logistics_weight_at_exit,
                'sale_logistics_exit_date_time': self.sale_logistics_exit_date_time,
            })
        return {'type': 'ir.actions.act_window_close'}
