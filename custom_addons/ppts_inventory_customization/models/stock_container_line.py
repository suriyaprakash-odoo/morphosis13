from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError


class StockFractionLine(models.TransientModel):
    _name = 'stock.fraction.line'
    _rec_name = 'project_id'

    fraction_id = fields.Many2one("project.fraction", string="Fraction")
    weight = fields.Float("Net Weight(Kg)", digits=(12,4))
    number_of_pieces = fields.Integer("Number of Pieces")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    production_cost = fields.Monetary('Production Cost', currency_field='currency_id')
    stock_container_id = fields.Many2one("stock.container", string="Stock Container")
    donor_container_id = fields.Many2one("project.container", string="Donor Container")
    project_id = fields.Many2one("project.entries", string="Project")
    is_cross_dock = fields.Boolean("Cross Dock")
    is_vrac = fields.Boolean("Vrac")
    location_id = fields.Many2one("stock.location", string="Location")
    state = fields.Selection([('open', 'Open'), ('to_be_sold', 'Closed/To Sale'), ('lead', 'Lead/Opportunity'),
                              ('second_process','Moved to Second Process'), ('sold', 'Sold'),('done',"Done")], string="State")

    @api.model
    def show_stock_container_lines(self):
        print ("==----------------------=======>>")
        fraction_line = self.env['fraction.line'].search([])
        lines = []
        for fl in fraction_line:
            if fl.container.active and  fl.fraction_id.project_id and not fl.container.cross_dock:
                fractions = self.env['stock.fraction.line'].create({
                    'fraction_id': fl.fraction_id.id,
                    'project_id': fl.fraction_id.project_id.id,
                    'stock_container_id': fl.container.id,
                    'production_cost': fl.production_cost,
                    'weight': fl.weight,
                    'is_vrac':fl.container.is_vrac,
                    'location_id': fl.container.location_id.id,
                    'state':fl.container.state
                })
                lines.append(fractions.id)

        for sct in self.env['stock.container'].search([]):
            if sct.active and sct.cross_dock:
                sc_fraction = self.env['stock.fraction.line'].create({
                    'project_id': sct.project_id.id,
                    'stock_container_id': sct.id,
                    'production_cost': sct.forecast_sale_price,
                    'weight': sct.net_weight,
                    'is_cross_dock': sct.cross_dock,
                    'location_id': sct.location_id.id,
                    'state':sct.state
                })
                lines.append(sc_fraction.id)

        return {
            'name': "Stock Container Line",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.fraction.line',
            'target': 'current',
            'domain': [('id', '=', [x for x in lines])],
            'context': {
                'search_default_group_project_id': True, 'search_default_group_stock_container_id': True,
            }
        }