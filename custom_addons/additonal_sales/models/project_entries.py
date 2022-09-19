from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'project.entries'

    sale_order_ids = fields.One2many("additional.sale.orders", "project_id", string="Purchase Orders")
    extra_sales_cost = fields.Monetary(compute='_compute_extra_sales', currency_field='currency_id', string="Additional Sales")
    estimated_extra_sales = fields.Monetary(currency_field='currency_id', string="Additional Sales")
    calculated_service_profit = fields.Monetary('Service Profit', currency_field='currency_id', compute='_compute_calculated_service_profit')

    @api.depends('sale_order_ids.untaxed_amount')
    def _compute_extra_sales(self):
        for project_entry in self:
            total = 0
            if project_entry.sale_order_ids:
                for sales in project_entry.sale_order_ids:
                    total += sales.untaxed_amount
            project_entry.update({
                'extra_sales_cost': total,
            })

    @api.depends('estimated_extra_sales','confirmed_transport_cost','labour_cost','extra_purchase_cost')
    def _compute_calculated_service_profit(self):
        for project in self:
            if project.estimated_extra_sales != 0:
                calculated_service_profit = project.estimated_extra_sales - (project.confirmed_transport_cost + project.labour_cost + project.extra_purchase_cost)
                print('---',calculated_service_profit,'---')
                project.update({
                        'calculated_service_profit' : calculated_service_profit
                    })
            else:
                project.update({
                        'calculated_service_profit' : 0.0
                    })


    def additional_sales_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['context'] = {
            'default_project_entree_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_company_id': self.company_id.id
        }
        action['domain'] = [('project_entree_id', '=', self.id)]
        so = self.env['sale.order'].search([('project_entree_id', '=', self.id)])
        if len(so) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = so.id
        return action


class AdditionalSale(models.Model):
    _name = 'additional.sale.orders'

    sale_id = fields.Many2one("sale.order", string="Sale Order")
    amount = fields.Float("Total Amount")
    untaxed_amount = fields.Float("Untaxed Amount")
    project_id = fields.Many2one("project.entries", string="Project ID")
    description = fields.Char("Description")

    @api.onchange('sale_id')
    def onchange_sale_id(self):
        if self.sale_id:
            self.amount = self.sale_id.amount_total
            self.untaxed_amount = self.sale_id.amount_untaxed
