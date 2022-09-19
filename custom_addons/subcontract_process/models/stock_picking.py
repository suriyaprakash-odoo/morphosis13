from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sub_contract_order = fields.Boolean("Subcontract Order")
    sub_type = fields.Selection([('internal', 'Internal'), ('outsource', 'Out Source')], string="Subcontract Type")


    @api.depends("state", "is_internal_purchase")
    def _compute_check_validate_button(self):
        if self.is_internal_purchase and self.state == "assigned":
            self.check_validate_button = True
        elif self.state == "sorted_treated":
            self.check_validate_button = True
        elif self.sub_contract_order and self.state == "assigned" and self.sub_type == 'internal':
            self.check_validate_button = True
        else:
            self.check_validate_button = False

    @api.depends("state", "is_internal_purchase", "picking_type_code")
    def _compute_check_update_container_outgoing_button(self):
        if not self.sub_contract_order and self.is_internal_purchase == False and self.state in ["assigned", "load_unload"] and self.picking_type_code == "outgoing":
            self.check_update_container_outgoing_button = True
        else:
            self.check_update_container_outgoing_button = False


    def action_done(self):
        res = super(StockPicking, self).action_done()

        if self.picking_type_id.sequence_code == 'OUT' and self.sub_contract_order:
            company_id = False
            location_id = False

            if self.partner_id.parent_id:
                company_id = self.env["res.company"].search([('partner_id','=',self.partner_id.parent_id.id)])

            elif self.env["res.company"].search([('partner_id', '=', self.partner_id.id)]):
                company_id = self.env["res.company"].search([('partner_id', '=', self.partner_id.id)])
            if company_id:
                location_id = self.env["stock.location"].search([('is_stock_location','=',True),('company_id','=',company_id.id),('usage','=','internal')])

            if location_id:
                for line in self.move_ids_without_package:
                    if line.container_ids:
                        for rec in line.container_ids:
                            rec.state = 'to_be_sold'
                            rec.location_id = location_id.id
            else:
                if self.sub_type == 'outsource':
                    for line in self.move_ids_without_package:
                        if line.container_ids:
                            for rec in line.container_ids:
                                rec.location_id = self.partner_id.property_stock_subcontractor.id
        return res