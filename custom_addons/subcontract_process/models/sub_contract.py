from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError

class MorphosisSubContract(models.Model):
    _name = 'subcontract.process'
    _description = 'Morphosis Sub Contract Process'


    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_sales_team(self, domain=None):
        team_id = self.env['crm.team'].search([('company_id', '=', self.env.company.id)
        ], limit=1)
        if not team_id and 'default_team_id' in self.env.context:
            team_id = self.env['crm.team'].browse(self.env.context.get('default_team_id'))
        if not team_id:
            team_domain = domain or []
            default_team_id = self.env['crm.team'].search(team_domain, limit=1)
            return default_team_id or self.env['crm.team']
        return team_id

    name = fields.Char()
    type = fields.Selection([('internal', 'Internal'), ('outsource', 'Out Source')], string="Subcontract Type")
    partner_id = fields.Many2one("res.partner", string="Subcontractor")
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    container_ids = fields.Many2many("stock.container", string='Containers', domain="[('state','in', ('subcontract','to_be_sold')),('related_company_id', '=', company_id)]")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    container_count = fields.Integer("Number of Containers", compute='_compute_container')
    net_weight = fields.Float("Container Net Weight(kg)", compute='_compute_container')
    production_cost = fields.Monetary('Production Cost', currency_field='currency_id', compute='_compute_production_price')
    state = fields.Selection([
        ('new', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string="state", default="new")

    sale_order_id = fields.Many2one("sale.order", string="Sale Order", copy=False)
    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order",copy=False)
    team_id = fields.Many2one("crm.team", string="Sales Team", default=_get_sales_team,domain="[('company_id', '=', company_id)]")


    def build_so_vals(self):
        so_vals ={}
        if self.type == 'internal':
            so_vals = {
                'partner_id': self.partner_id.id or False,
                'order_line': [],
                'sub_contract': True,
                'sale_by':'container',
                'internal_sales':True,
                'team_id':self.team_id.id
            }
        else:
            so_vals = {
                'partner_id': self.partner_id.id or False,
                'order_line': [],
                'sub_contract': True,
                'sale_by': 'container',
                'team_id': self.team_id.id
            }

        rc_product_list = []
        for line in self.container_ids:
            if line.content_type_id.id not in rc_product_list:
                rc_product_list.append(line.content_type_id.id)

        rc_vals = []
        for rec in rc_product_list:
            weight = 0.0
            final_weight = 0.0
            rc_line = {}
            container_obj = self.env['stock.container'].search([('content_type_id', '=', rec), ('id', 'in', self.container_ids.ids)])
            product_obj = self.env['product.product'].search([('id', '=', rec)])
            for line in container_obj:
                if line.container_specific == "weight":
                    weight += line.net_weight

                    if line.content_type_id.uom_id.name == 'Tonne' or line.content_type_id.uom_id.name == 'tonne':
                        final_weight = weight / 1000
                    else:
                        final_weight = weight
                else:
                    final_weight += line.total_number_of_pieces

            rc_line.update({
                'product_id': product_obj.id,
                'name': product_obj.name,
                'product_uom': product_obj.uom_id.id,
                'product_uom_qty': final_weight,
                'container_id': container_obj.ids,
            })
            rc_vals.append((0, 0, rc_line))
        so_vals['order_line'] = rc_vals

        return so_vals

    def action_create_sale_order(self):
        so_vals = self.build_so_vals()
        sale_id = self.env["sale.order"].create(so_vals)
        self.sale_order_id = sale_id
        self.state = 'processing'

        for line in self.container_ids:
            line.state = 'subcontract'


    def action_cancel(self):
        if self.state == 'processing':
            if self.sale_order_id:
                self.sale_order_id.action_cancel()
            if self.purchase_order_id:
                self.purchase_order_id.button_cancel()
            self.state = 'cancel'
        else:
            self.state = 'cancel'

        for line in self.container_ids:
            line.state = 'to_be_sold'


    @api.depends('container_ids')
    def _compute_production_price(self):
        for rc in self:
            production_cost = 0.0
            if rc.container_ids:
                for line in rc.container_ids:
                    production_cost += line.forecast_sale_price
                    rc.update({
                        'production_cost': production_cost,
                    })
            else:
                rc.update({
                    'production_cost': production_cost,
                })

    @api.depends('container_ids')
    def _compute_container(self):
        for rc in self:
            container_count = 0
            net_weight = 0.0

            for record in rc.container_ids:
                net_weight += record.net_weight
            if rc.container_ids:
                container_count = len(rc.container_ids)
            else:
                container_count = container_count
                net_weight = net_weight

            rc.update({
                'container_count': container_count,
                'net_weight': net_weight,
            })

    @api.onchange('type')
    def _onchange_project_id(self):
        if self.type=='internal':
            return {
                'domain': {'partner_id': [('internal_company', '=', True)], 'location_id' : [('usage','=','internal')]}
            }
        else:
            return {
                'domain':{'partner_id': [],'location_id' : []}
            }


    @api.model
    def create(self, vals):

        company_partner = self.env["res.company"].browse(vals.get('company_id')).partner_id.id
        if vals.get("partner_id") == company_partner:
            raise UserError('You can not create subcontract for same company')

        vals['name'] = self.env['ir.sequence'].next_by_code('subcontract.seq') or '/'

        return super(MorphosisSubContract, self).create(vals)

    def open_sale_order(self):
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'views_id': False,
            'views': [(self.env.ref('sale.view_order_form').id or False, 'form')],
        }


    def open_purchase_order(self):
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'views_id': False,
            'views': [(self.env.ref('purchase.purchase_order_form').id or False, 'form')],
        }


class StockContainer(models.Model):
    _inherit = 'stock.container'

    # state = fields.Selection([('open', 'Open'), ('to_be_sold', 'Closed/To Sale'), ('lead', 'Lead/Opportunity'),('second_process', 'Moved to Second Process'), ('sold', 'Sold'), ('taf', 'TAF'),('done', "Done")], string="State", default='open', tracking=True)
