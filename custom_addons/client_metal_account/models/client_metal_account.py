from odoo import fields, models, api


class ClientMetalAccount(models.Model):
    _name = 'client.metal.account'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one("res.partner", string="Client")
    metal_line_ids = fields.One2many("metal.account.line", "metal_acc_id", string="Client Metal Line")


class MetalAccountLine(models.Model):
    _name = "metal.account.line"

    project_id = fields.Many2one("project.entries", string="Project ID", required=1)
    metal = fields.Char("Metal", required=1)
    product_id = fields.Many2one("product.product", string="Product", required=1)
    quantity = fields.Float("Quantity(g)", required=1)
    location_id = fields.Many2one("stock.location", string="Location", required=1)
    metal_acc_id = fields.Many2one("client.metal.account")
    commission = fields.Float("Commission")
    lot_id = fields.Many2one("stock.production.lot", string="LOT/Serial", domain="[('product_id', '=', product_id)]", check_company=True)


class MetalAccWizard(models.TransientModel):
    _name = 'metal.acc.wizard'

    project_id = fields.Many2one("project.entries", string="Project ID", required=1)
    partner_id = fields.Many2one("res.partner", string="Client", required=1)
    metal_wizard_line = fields.One2many("metal.acc.wizard.line", 'wiz_id', string="Metal Line")

    def credit_to_client_account(self):
        line_item = []
        client_metal_line = self.env['client.metal.account'].search([('partner_id', '=', self.partner_id.id)])
        final_quantity = 0.0
        final_commission = 0.0
        if client_metal_line:
            for wiz_line in self.metal_wizard_line:
                flag = False

                if wiz_line.product_id.uom_id.uom_type == 'bigger':
                    final_quantity = wiz_line.to_client / wiz_line.product_id.uom_id.factor_inv
                    final_commission = wiz_line.commission / wiz_line.product_id.uom_id.factor_inv
                elif wiz_line.product_id.uom_id.uom_type == 'smaller':
                    final_quantity = wiz_line.to_client * wiz_line.product_id.uom_id.factor
                    final_commission = wiz_line.commission * wiz_line.product_id.uom_id.factor
                else:
                    final_quantity = wiz_line.to_client
                    final_commission = wiz_line.commission

                for metal_line in client_metal_line.metal_line_ids:
                    if metal_line.project_id.id == wiz_line.project_id.id and metal_line.product_id.id == wiz_line.product_id.id:
                        flag = True
                        if metal_line.quantity != wiz_line.to_client:
                            metal_line.quantity = wiz_line.to_client
                            metal_line.lot_id = wiz_line.lot_id.id
                            client_stock = {
                                'product_id': wiz_line.product_id.id,
                                'location_id': wiz_line.location_id.id,
                                'quantity': final_quantity,
                                'lot_id': wiz_line.lot_id.id,
                                'owner_id': self.partner_id.id
                            }
                            self.env["stock.quant"].sudo().create(client_stock)
                        if metal_line.commission != wiz_line.commission:
                            metal_line.commission = wiz_line.commission
                            metal_line.lot_id = wiz_line.lot_id.id
                            commission_stock = {
                                'product_id': wiz_line.product_id.id,
                                'location_id': self.project_id.company_id.precious_location_id.id,
                                'quantity': final_commission,
                                'owner_id': wiz_line.company_id.partner_id.id,
                            }
                            self.env["stock.quant"].sudo().create(commission_stock)
                if not flag:
                    self.env['metal.account.line'].create({
                        'project_id': self.project_id.id,
                        'quantity': wiz_line.to_client,
                        'location_id': wiz_line.location_id.id,
                        'metal': wiz_line.metal,
                        'product_id': wiz_line.product_id.id,
                        'metal_acc_id': client_metal_line.id,
                        'commission': wiz_line.commission,
                        'lot_id': wiz_line.lot_id.id
                    })

                    client_stock_line = {
                        'product_id': wiz_line.product_id.id,
                        'location_id': wiz_line.location_id.id,
                        'quantity': final_quantity,
                        'lot_id': wiz_line.lot_id.id,
                        'owner_id': self.partner_id.id
                    }
                    self.env["stock.quant"].sudo().create(client_stock_line)

                    commission_stock_line = {
                        'product_id': wiz_line.product_id.id,
                        'location_id': self.project_id.company_id.precious_location_id.id,
                        'quantity': final_commission,
                        'owner_id': wiz_line.company_id.partner_id.id,
                    }
                    self.env["stock.quant"].sudo().create(commission_stock_line)
        else:
            for line in self.metal_wizard_line:
                client_stock_vals = {
                    'product_id': line.product_id.id,
                    'location_id': line.location_id.id,
                    'quantity': final_quantity,
                    'lot_id': line.lot_id.id,
                    'owner_id': self.partner_id.id
                }
                self.env["stock.quant"].sudo().create(client_stock_vals)

                commission_stock_vals = {
                    'product_id': line.product_id.id,
                    'location_id': self.project_id.company_id.precious_location_id.id,
                    'quantity': final_commission,
                    'owner_id': line.company_id.partner_id.id,
                }
                self.env["stock.quant"].sudo().create(commission_stock_vals)

                line_item.append((0, 0, {
                    'project_id': self.project_id.id,
                    'quantity': line.to_client,
                    'location_id': line.location_id.id,
                    'metal': line.metal,
                    'product_id': line.product_id.id,
                    'commission': line.commission,
                    'lot_id': line.lot_id.id
                }))

            metal_acc_id = self.env['client.metal.account'].create({'partner_id': self.partner_id.id, 'metal_line_ids': line_item})
            self.project_id.metal_account_id = metal_acc_id


class MetalAccWizardLine(models.TransientModel):
    _name = 'metal.acc.wizard.line'

    wiz_id = fields.Many2one("metal.acc.wizard")
    project_id = fields.Many2one("project.entries", string="Project ID")
    partner_id = fields.Many2one("res.partner", string="Client")
    product_id = fields.Many2one("product.product", string="Product")
    metal = fields.Char("Metal")
    actual_result = fields.Float("Result(g)")
    to_client = fields.Float("Client Metal Account(g)")
    location_id = fields.Many2one("stock.location", string="Location")
    commission = fields.Float("Commission")
    lot_id = fields.Many2one("stock.production.lot", string="LOT/Serial", domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one("res.company", string="Company")


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    @api.onchange('location_src_id', 'routing_id')
    def _onchange_location(self):
        source_location = self.location_src_id
        self.move_raw_ids.update({
            'warehouse_id': source_location.get_warehouse().id,
            'location_id': source_location.id,
        })
