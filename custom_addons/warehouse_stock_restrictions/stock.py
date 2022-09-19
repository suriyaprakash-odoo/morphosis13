# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Default Warehouse Operations')
    
    
    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)

        if vals.get("stock_location_ids"):
            if res.stock_location_ids:
                for location in res.stock_location_ids:
                    location.compute_access_user_ids()
        return res

    def write(self, vals):
        actual_stock_location_ids = self.stock_location_ids.ids
        
        if vals.get("stock_location_ids"):
            updated_stock_location_ids = vals.get("stock_location_ids")[0][2]
        
            final_stock_location_ids_added = list(set(updated_stock_location_ids) - set(actual_stock_location_ids))
            final_stock_location_ids_removed = list(set(actual_stock_location_ids) - set(updated_stock_location_ids))

            final_stock_location_ids = final_stock_location_ids_added + final_stock_location_ids_removed

        res = super(ResUsers, self).write(vals)
        if vals.get("stock_location_ids"):
            if final_stock_location_ids:
                for location_id in final_stock_location_ids:
                    location_obj = self.env['stock.location'].sudo().browse(location_id).compute_access_user_ids()
        return res


class StockLocation(models.Model):
    _inherit = 'stock.location'

    access_user_ids = fields.Many2many(comodel_name='res.users',string="User Access")


    trigger_access_user_ids = fields.Boolean(compute="_compute_trigger_access_user_ids")

    def _compute_trigger_access_user_ids(self):

        for location in self:
            location.trigger_access_user_ids = True
            get_users = self.env['res.users'].sudo().search([('stock_location_ids','=',location.id)])

            location.access_user_ids = get_users
    
    def compute_access_user_ids(self):
        for location in self:
            get_users = self.env['res.users'].sudo().search([('stock_location_ids','=',location.id)])

            location.access_user_ids = get_users


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        for rec in self:
            if rec.state == 'draft':
                return True
            user_locations = self.env.user.stock_location_ids
            print(user_locations)
            print("Checking access %s" %self.env.user.default_picking_type_ids)
            if self.env.user.restrict_locations:
                message = _(
                    'Invalid Location. You cannot process this move since you do '
                    'not control the location "%s". '
                    'Please contact your Adminstrator.')
                if rec.location_id not in user_locations:
                    raise Warning(message % rec.location_id.name)
                elif rec.location_dest_id not in user_locations:
                    raise Warning(message % rec.location_dest_id.name)


