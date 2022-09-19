from odoo import api, fields, models,_
from odoo.exceptions import UserError


class StockStatus(models.TransientModel):
    _name = 'stock.status'

    def show_stock_status(self):
        dc_containers = self.env["project.container"].search([('state','not in',('close','return')),('is_child_container','=',False)])
        containers = []
        for dc in dc_containers:
            dcs = self.env['stock.status.line'].create({
                'name': dc.name,
                'gross_weight' : dc.gross_weight,
                'net_weight' : dc.net_gross_weight,
                'volume': dc.volume,
                'primary_id': dc.main_product_id.id,
                'secondary_id': dc.sub_product_id.id,
                'type': 'Donor Containers',
                'stock_value' : dc.spot_value,
                'remaining_weight': dc.remaining_weight
            })
            containers.append(dcs.id)
        rc_containers = self.env["stock.container"].search([('state', 'not in', ('sold', 'done'))])
        for rc in rc_containers:

            rcs = self.env['stock.status.line'].create({
                'name': rc.name,
                'gross_weight': rc.gross_weight,
                'net_weight': rc.net_weight,
                'volume': rc.volume,
                'primary_id': rc.primary_content_type_id.id,
                'secondary_id': rc.content_type_id.id,
                'type':'Recipient Containers',
                'stock_value': rc.forecast_sale_price
            })
            containers.append(rcs.id)

        tree_id = self.env.ref('stock_volume_report.stock_status_tree_view').id

        return {
            'name': _('Stock Status'),
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', [x for x in containers])],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.status.line',
            'view_id': False,
            'views': [(tree_id, 'tree')],
            'target': 'current',
            'context': {
                'search_default_group_container_type': True, 'search_default_group_primary_id': True, 'search_default_group_secondary_id': True,
            }
        }


class StockStatusLine(models.TransientModel):
    _name = 'stock.status.line'

    name = fields.Char("Container")
    gross_weight =fields.Float("Gross Weight")
    net_weight = fields.Float("Net Weight")
    volume = fields.Float("Volume")
    rc = fields.Boolean("RC")
    primary_id = fields.Many2one('product.template', string='Primary Content Type')
    secondary_id = fields.Many2one('product.product', string='Secondary Content Type')
    type = fields.Selection([('Recipient Containers', 'Recipient Containers'), ('Donor Containers', 'Donor Containers')], string="Container Type")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    stock_value = fields.Monetary('Stock Value', currency_field='currency_id')
    remaining_weight = fields.Float("Remaining Weight")