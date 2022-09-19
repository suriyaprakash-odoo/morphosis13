from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ProjectEntries(models.Model):
    _inherit = 'project.entries'

    metal_account_id = fields.Many2one("client.metal.account")

    def open_client_metal_acc(self):
        return {
            'name': _('Client Metal Account'),
            'type': 'ir.actions.act_window',
            'res_id': self.metal_account_id.id,
            'view_mode': 'form',
            'res_model': 'client.metal.account',
            'views_id': False,
            'views': [(self.env.ref('client_metal_account.view_client_metal_account_form').id, 'form')],
        }

    def validate_refining(self):
        if self.silver or self.gold or self.palladium or self.platinum or self.copper or self.rhodium or self.ruthenium or self.iridium:
            metal_lines = []
            if self.silver:
                silver = self.env["product.product"].search([('precious_metal', '=', 'silver')], limit=1)
                sl_actual=0.0
                sl_actual_pr = 0.0
                sl_commission = 0.0
                sl_levy = 0.0

                for line in self.silver_cost_ids:
                    sl_actual += line.actual_result
                    sl_actual_pr += ((100 - line.dedection_percentage)*line.actual_result)/100
                    sl_commission += (line.dedection_percentage*line.actual_result)/100
                    sl_levy += line.minimum_levy

                if sl_commission <  sl_levy:
                    sl_to_client = sl_actual - sl_levy
                    commission_sl = sl_levy
                else:
                    sl_to_client = sl_actual_pr
                    commission_sl = sl_commission

                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : silver.id or False,
                    'metal': "Silver",
                    'actual_result' : sl_actual,
                    'to_client' : sl_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_sl,
                    'company_id': self.company_id.id
                }))

            if self.gold:
                gold = self.env["product.product"].search([('precious_metal', '=', 'gold')], limit=1)
                gl_actual=0.0
                gl_actual_pr = 0.0
                gl_commission = 0.0
                gl_levy = 0.0
                for gl_line in self.gold_cost_ids:
                    gl_actual += gl_line.actual_result
                    gl_actual_pr += ((100 - gl_line.dedection_percentage)*gl_line.actual_result)/100
                    gl_commission += (gl_line.dedection_percentage * gl_line.actual_result) / 100
                    gl_levy += gl_line.minimum_levy

                if gl_commission < gl_levy:
                    gl_to_client = gl_actual - gl_levy
                    commission_gl = gl_levy
                else:
                    gl_to_client = gl_actual_pr
                    commission_gl = gl_commission

                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : gold.id or False,
                    'metal': "Gold",
                    'actual_result' : gl_actual,
                    'to_client' : gl_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission': commission_gl,
                    'company_id': self.company_id.id
                }))

            if self.palladium:
                palladium = self.env["product.product"].search([('precious_metal', '=', 'palladium')], limit=1)
                pl_actual=0.0
                pl_actual_pr = 0.0
                pl_commission = 0.0
                pl_levy = 0.0
                for pl_line in self.palladium_cost_ids:
                    pl_actual += pl_line.actual_result
                    pl_actual_pr += ((100 - pl_line.dedection_percentage)*pl_line.actual_result)/100
                    pl_commission += (pl_line.dedection_percentage * pl_line.actual_result) / 100
                    pl_levy += pl_line.minimum_levy

                if pl_commission < pl_levy:
                    pl_to_client = pl_actual - pl_levy
                    commission_pl = pl_levy
                else:
                    pl_to_client = pl_actual_pr
                    commission_pl = pl_commission

                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : palladium.id or False,
                    'metal': "Palladium",
                    'actual_result' : pl_actual,
                    'to_client' : pl_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_pl,
                    'company_id': self.company_id.id
                }))


            if self.platinum:
                platinum = self.env["product.product"].search([('precious_metal', '=', 'platinum')], limit=1)
                pt_actual=0.0
                pt_actual_pr = 0.0
                pt_commission = 0.0
                pt_levy = 0.0
                for pt_line in self.platinum_cost_ids:
                    pt_actual += pt_line.actual_result
                    pt_actual_pr += ((100 - pt_line.dedection_percentage)*pt_line.actual_result)/100
                    pt_commission += (pt_line.dedection_percentage * pt_line.actual_result) / 100
                    pt_levy += pt_line.minimum_levy

                if pt_commission < pt_levy:
                    pt_to_client = pt_actual - pt_levy
                    commission_pt = pt_levy
                else:
                    pt_to_client = pt_actual_pr
                    commission_pt = pt_commission

                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : platinum.id or False,
                    'metal': "Platinum",
                    'actual_result' : pt_actual,
                    'to_client' : pt_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_pt,
                    'company_id': self.company_id.id
                }))

            if self.copper_cost_ids:
                copper = self.env["product.product"].search([('precious_metal', '=', 'copper')], limit=1)
                cp_actual=0.0
                cp_actual_pr = 0.0
                cp_commission = 0.0
                cp_levy = 0.0

                for cp_line in self.copper_cost_ids:
                    cp_actual += cp_line.actual_result
                    cp_actual_pr += ((100 - cp_line.dedection_percentage)*cp_line.actual_result)/100
                    cp_commission += (cp_line.dedection_percentage * cp_line.actual_result) / 100
                    cp_levy += cp_line.minimum_levy

                if cp_commission < cp_levy:
                    cp_to_client = cp_actual - cp_levy
                    commission_cp = cp_levy
                else:
                    cp_to_client = cp_actual_pr
                    commission_cp = cp_commission


                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : copper.id or False,
                    'metal': "Copper",
                    'actual_result' : cp_actual,
                    'to_client' : cp_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_cp,
                    'company_id': self.company_id.id
                }))

            if self.rhodium_cost_ids:
                rhodium = self.env["product.product"].search([('precious_metal', '=', 'rhodium')], limit=1)
                rh_actual=0.0
                rh_actual_pr = 0.0
                rh_commission = 0.0
                rh_levy = 0.0

                for rh_line in self.rhodium_cost_ids:
                    rh_actual += rh_line.actual_result
                    rh_actual_pr += ((100 - rh_line.dedection_percentage)*rh_line.actual_result)/100
                    rh_commission += (rh_line.dedection_percentage * rh_line.actual_result) / 100
                    rh_levy += rh_line.minimum_levy

                if rh_commission < rh_levy:
                    rh_to_client = rh_actual - rh_levy
                    commission_rh = rh_levy
                else:
                    rh_to_client = rh_actual_pr
                    commission_rh = rh_commission

                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : rhodium.id or False,
                    'metal': "Rhodium",
                    'actual_result' : rh_actual,
                    'to_client' : rh_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_rh,
                    'company_id': self.company_id.id
                }))

            if self.ruthenium_cost_ids:
                ruthenium = self.env["product.product"].search([('precious_metal', '=', 'ruthenium')], limit=1)
                ru_actual=0.0
                ru_actual_pr = 0.0
                ru_commission = 0.0
                ru_levy = 0.0

                for ru_line in self.rhodium_cost_ids:
                    ru_actual += ru_line.actual_result
                    ru_actual_pr += ((100 - ru_line.dedection_percentage)*ru_line.actual_result)/100
                    ru_commission += (ru_actual.dedection_percentage * ru_actual.actual_result) / 100
                    ru_levy += ru_line.minimum_levy

                if ru_commission < ru_levy:
                    ru_to_client = ru_actual - ru_levy
                    commission_ru = ru_levy
                else:
                    ru_to_client = ru_actual_pr
                    commission_ru = ru_commission

                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : ruthenium.id or False,
                    'metal': "Ruthenium",
                    'actual_result' : ru_actual,
                    'to_client' : ru_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_ru,
                    'company_id': self.company_id.id
                }))


            if self.iridium_cost_ids:
                iridium = self.env["product.product"].search([('precious_metal', '=', 'iridium')], limit=1)
                ir_actual=0.0
                ir_actual_pr = 0.0
                ir_commission = 0.0
                ir_levy = 0.0
                for ir_line in self.iridium_cost_ids:
                    ir_actual += ru_line.actual_result
                    ir_actual_pr += ((100 - ir_line.dedection_percentage)* ir_line.actual_result)/100
                    ir_commission += (ir_line.dedection_percentage * ir_line.actual_result) / 100
                    ir_levy += ir_line.minimum_levy

                if ir_commission < ir_levy:
                    ir_to_client = ir_actual - ir_levy
                    commission_ir = ir_levy
                else:
                    ir_to_client = ir_actual_pr
                    commission_ir = ir_commission
                metal_lines.append((0, 0, {
                    'project_id':self.id,
                    'partner_id':self.partner_id.id,
                    'product_id' : iridium.id or False,
                    'metal': "Iridium",
                    'actual_result' : ir_actual,
                    'to_client' : ir_to_client,
                    'location_id': self.partner_id.metal_location_id.id or False,
                    'commission':commission_ir,
                    'company_id': self.company_id.id
                }))

            attach_value = {'partner_id': self.partner_id.id,'project_id':self.id,'metal_wizard_line':metal_lines}
            rec_id = self.env['metal.acc.wizard'].create(attach_value)

            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'metal.acc.wizard',
                'res_id': rec_id.id,
                'target': 'new',
            }
        else:
            raise UserError(_('Please some metals to the line item'))


class StockContainer(models.Model):
    _inherit = 'stock.container'

    @api.onchange('content_type_id')
    def _onchange_content_type_id(self):
        if self.content_type_id:
            if self.content_type_id.categ_id.is_metal:
                self.location_id = self.content_type_id.categ_id.precious_location_id.id