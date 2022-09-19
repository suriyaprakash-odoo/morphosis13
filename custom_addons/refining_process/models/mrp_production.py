from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class Production(models.Model):
    _inherit = 'mrp.production'

    container_id = fields.Many2one("project.container", string="Container", readonly=1)
    project_id = fields.Many2one("project.entries", string="Project ID", readonly=1)
    silver = fields.Boolean("Silver")
    gold = fields.Boolean("Gold")
    palladium = fields.Boolean("Palladium")
    platinum = fields.Boolean("Platinum")
    copper = fields.Boolean("Copper")
    rhodium = fields.Boolean("Rhodium")
    ruthenium = fields.Boolean("Ruthenium")
    iridium = fields.Boolean("iridium")
    silver_cost_ids = fields.One2many('silver.refining.cost', 'silver_cost_mo', string="Silver Refining cost line")
    gold_cost_ids = fields.One2many('gold.refining.cost', 'gold_cost_mo', string="Gold Refining cost line")
    palladium_cost_ids = fields.One2many('palladium.refining.cost', 'palladium_cost_mo', string="Palladium Refining cost line")
    platinum_cost_ids = fields.One2many('platinum.refining.cost', 'platinum_cost_mo', string="Platinum Refining cost line")
    copper_cost_ids = fields.One2many('copper.refining.cost', 'copper_cost_mo', string="Copper Refining cost line")
    rhodium_cost_ids = fields.One2many('rhodium.refining.cost', 'rhodium_cost_mo', string="Rhodium Refining cost line")
    ruthenium_cost_ids = fields.One2many('ruthenium.refining.cost', 'ruthenium_cost_mo', string="Ruthenium Refining cost line")
    iridium_cost_ids = fields.One2many('iridium.refining.cost', 'iridium_cost_mo', string="Iridium Refining cost line")
    operation_cost_ids = fields.One2many("mrp.cost.operations","mrp_id", string="Operation Cost")
    cost_structure_ids = fields.One2many("mrp.cost.structure","mrp_id", string="Cost Structure")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    total_structure_cost = fields.Monetary("Structure Cost Total",digits=(12,4), currency_field='currency_id', compute='find_total_structure_cost')
    total_operation_cost = fields.Monetary("Operation Cost Total",digits=(12,4), currency_field='currency_id', compute='find_total_operation_cost')
    production_total = fields.Monetary("Total Production Cost",digits=(12,4), currency_field='currency_id', compute='find_total_production_cost')
    is_refining = fields.Boolean("Is Refining")

    @api.depends('total_structure_cost','total_operation_cost')
    def find_total_production_cost(self):
        for rec in self:
            rec.update({
                'production_total': rec.total_structure_cost + rec.total_operation_cost
            })

    @api.depends('cost_structure_ids')
    def find_total_structure_cost(self):
        for rec in self:
            total= 0.0
            for line in rec.cost_structure_ids:
                total += line.total
            rec.update({
                'total_structure_cost': total
            })

    @api.depends('operation_cost_ids')
    def find_total_operation_cost(self):
        for rec in self:
            total = 0.0
            for line in rec.operation_cost_ids:
                total += line.total_cost
            rec.update({
                'total_operation_cost': total
            })


    def get_report_values(self):
        ProductProduct = self.env['product.product']
        StockMove = self.env['stock.move']
        res = []
        for product in self.mapped('product_id'):
            mos = self.filtered(lambda m: m.product_id == product)
            total_cost = 0.0

            #get the cost of operations
            operations = []
            Workorders = self.env['mrp.workorder'].search([('production_id', 'in', mos.ids)])
            if Workorders:
                query_str = """SELECT w.operation_id, op.name, partner.name, sum(t.duration), wc.costs_hour
                                FROM mrp_workcenter_productivity t
                                LEFT JOIN mrp_workorder w ON (w.id = t.workorder_id)
                                LEFT JOIN mrp_workcenter wc ON (wc.id = t.workcenter_id )
                                LEFT JOIN res_users u ON (t.user_id = u.id)
                                LEFT JOIN res_partner partner ON (u.partner_id = partner.id)
                                LEFT JOIN mrp_routing_workcenter op ON (w.operation_id = op.id)
                                WHERE t.workorder_id IS NOT NULL AND t.workorder_id IN %s
                                GROUP BY w.operation_id, op.name, partner.name, t.user_id, wc.costs_hour
                                ORDER BY op.name, partner.name
                            """
                self.env.cr.execute(query_str, (tuple(Workorders.ids), ))
                for op_id, op_name, user, duration, cost_hour in self.env.cr.fetchall():
                    user_id = self.env["res.users"].search([("name",'=', user)])
                    self.env['mrp.cost.operations'].create({'user_id':user_id.id,'operation_id':op_id,'work_time':duration/ 60.0,'cost':cost_hour,'mrp_id':self.id})
                    operations.append([user, op_id, op_name, duration / 60.0, cost_hour])

            #get the cost of raw material effectively used
            raw_material_moves = []
            query_str = """SELECT sm.product_id, sm.bom_line_id, abs(SUM(svl.quantity)), abs(SUM(svl.value))
                             FROM stock_move AS sm
                       INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                            WHERE sm.raw_material_production_id in %s AND sm.state != 'cancel' AND sm.product_qty != 0 AND scrapped != 't'
                         GROUP BY sm.bom_line_id, sm.product_id"""
            self.env.cr.execute(query_str, (tuple(mos.ids), ))
            for product_id, bom_line_id, qty, cost in self.env.cr.fetchall():
                raw_material_moves.append({
                    'qty': qty,
                    'cost': cost,
                    'product_id': ProductProduct.browse(product_id),
                    'bom_line_id': bom_line_id
                })
                total_cost += cost
                self.env['mrp.cost.structure'].create({'qty': qty,'cost': cost,'bom_line': bom_line_id, 'mrp_id': self.id})

            #get the cost of scrapped materials
            scraps = StockMove.search([('production_id', 'in', mos.ids), ('scrapped', '=', True), ('state', '=', 'done')])
            uom = mos and mos[0].product_uom_id
            mo_qty = 0
            if not all(m.product_uom_id.id == uom.id for m in mos):
                uom = product.uom_id
                for m in mos:
                    qty = sum(m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id == product).mapped('product_qty'))
                    if m.product_uom_id.id == uom.id:
                        mo_qty += qty
                    else:
                        mo_qty += m.product_uom_id._compute_quantity(qty, uom)
            else:
                for m in mos:
                    mo_qty += sum(m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id == product).mapped('product_qty'))
            for m in mos:
                byproduct_moves = m.move_finished_ids.filtered(lambda mo: mo.state != 'cancel' and mo.product_id != product)
            res.append({
                # 'product': product,
                # 'mo_qty': mo_qty,
                # 'mo_uom': uom,
                # 'operations': operations,
                'currency': self.env.company.currency_id,
                # 'raw_material_moves': raw_material_moves,
                'total_cost': total_cost,
                'scraps': scraps,
                'mocount': len(mos),
                'byproduct_moves': byproduct_moves
            })
        return res


    @api.onchange('project_id')
    def onchange_refining_project_id(self):
        if self.project_id and self.project_id.project_type == 'refine':
            self.is_refining = True
            if self.project_id.silver_cost_ids:
                self.silver_cost_ids = self.project_id.silver_cost_ids
                self.silver = True
            if self.project_id.gold_cost_ids:
                self.gold_cost_ids = self.project_id.gold_cost_ids
                self.gold = True
            if self.project_id.palladium_cost_ids:
                self.palladium_cost_ids = self.project_id.palladium_cost_ids
                self.palladium = True
            if self.project_id.platinum_cost_ids:
                self.platinum_cost_ids = self.project_id.platinum_cost_ids
                self.platinum = True
            if self.project_id.copper_cost_ids:
                self.copper_cost_ids = self.project_id.copper_cost_ids
                self.copper = True
            if self.project_id.rhodium_cost_ids:
                self.rhodium_cost_ids = self.project_id.rhodium_cost_ids
                self.rhodium = True
            if self.project_id.ruthenium_cost_ids:
                self.ruthenium_cost_ids = self.project_id.ruthenium_cost_ids
                self.ruthenium = True
            if self.project_id.iridium_cost_ids:
                self.iridium_cost_ids = self.project_id.iridium_cost_ids
                self.iridium = True

    @api.onchange('silver','gold','palladium','platinum','copper','rhodium','ruthenium','iridium')
    def onchange_silver(self):
        if self.silver:
            self.project_id.silver = True
        else:
            self.project_id.silver = False

        if self.gold:
            self.project_id.gold = True
        else:
            self.project_id.gold = False

        if self.palladium:
            self.project_id.palladium = True
        else:
            self.project_id.palladium = False

        if self.platinum:
            self.project_id.platinum = True
        else:
            self.project_id.platinum = False

        if self.copper:
            self.project_id.copper = True
        else:
            self.project_id.copper = False

        if self.rhodium:
            self.project_id.rhodium = True
        else:
            self.project_id.rhodium = False

        if self.ruthenium:
            self.project_id.ruthenium = True
        else:
            self.project_id.ruthenium = False

        if self.iridium:
            self.project_id.iridium = True
        else:
            self.project_id.iridium = False


    @api.model
    def create(self, vals):
        res = super(Production, self).create(vals)
        if res.container_id:
            res.container_id.production_id = res.id
            res.container_id.state = 'manufacturing'
        return res

    def button_mark_done(self):
        res = super().button_mark_done()
        if self.container_id:
            self.container_id.state = 'close'
        self.get_report_values()
        return res


class SilverRefiningCost(models.Model):
    _inherit = "silver.refining.cost"

    silver_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")


class GoldRefiningCost(models.Model):
    _inherit = "gold.refining.cost"

    gold_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")


class PalladiumRefiningCost(models.Model):
    _inherit = "palladium.refining.cost"

    palladium_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")


class PlatinumRefiningCost(models.Model):
    _inherit = "platinum.refining.cost"

    platinum_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")


class CopperRefiningCost(models.Model):
    _inherit = "copper.refining.cost"

    copper_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")



class RhodiumRefiningCost(models.Model):
    _inherit = "rhodium.refining.cost"

    rhodium_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")


class RutheniumRefiningCost(models.Model):
    _inherit = "ruthenium.refining.cost"

    ruthenium_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")


class IridiumRefiningCost(models.Model):
    _inherit = "iridium.refining.cost"

    iridium_cost_mo = fields.Many2one('mrp.production', string="Manufacturing Order")



class MrpCostStructure(models.Model):
    _name = 'mrp.cost.structure'

    bom_line = fields.Many2one("mrp.bom.line", string="Component")
    qty = fields.Float("Quantity", digits=(12,6))
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    cost =fields.Monetary("Unit Cost",digits=(12,4),currency_field='currency_id')
    total = fields.Monetary("Total Cost", compute='_find_total',digits=(12,4),currency_field='currency_id')
    mrp_id = fields.Many2one("mrp.production", string="MO ID")

    @api.depends('qty','cost')
    def _find_total(self):
        for rec in self:
            rec.update({
                'total': rec.cost * rec.qty
            })


class MrpCostOperations(models.Model):
    _name = 'mrp.cost.operations'

    user_id = fields.Many2one("res.users", string="Operator")
    operation_id = fields.Many2one("mrp.routing.workcenter", string="Operation")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    work_time = fields.Float("Working Time", digits=(12,4))
    cost = fields.Monetary("Cost/Hour",digits=(12,4))
    total_cost = fields.Monetary("Total", compute='_find_total_cost',digits=(12,4),currency_field='currency_id')
    mrp_id = fields.Many2one("mrp.production", string="MO ID")


    @api.depends('work_time', 'cost')
    def _find_total_cost(self):
        for rec in self:
            rec.update({
                'total_cost': rec.work_time * rec.cost
            })