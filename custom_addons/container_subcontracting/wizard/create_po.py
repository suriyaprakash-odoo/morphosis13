from odoo import api, fields, models
from datetime import datetime

class CreateSubContractPo(models.TransientModel):
    _name = 'create.po'

    partner_id = fields.Many2one("res.partner", string="Vendor")
    po_lines = fields.One2many("create.po.line","wiz_id",string="Purchase Order Line")
    container_id = fields.Many2one("project.container",string="Container ID")

    def create_sbc_purchase_order(self):
        line_vals = []
        picking_type_id = self.env["stock.picking.type"].search([('code', '=', 'incoming'), ('sequence_code', '=', 'IN'), ('company_id', '=', self.container_id.project_id.company_id.id)], limit=1)

        for line in self.po_lines:
            line_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_qty': line.qty,
                'price_unit': line.price,
                'product_uom': line.uom_id.id,
                'date_planned': datetime.now().date()
            }))

        po_id = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'company_id': self.container_id.company_id.id,
            'order_line': line_vals,
            'origin': self.container_id.project_id.name,
            'project_entry_id': self.container_id.project_id.id,
            'is_internal_purchase': True,
            'picking_type_id':picking_type_id.id,
        })
        po_id.button_confirm()
        self.container_id.sub_contract_po_id = po_id.id



        picking_type = self.env["stock.picking.type"].search([('code', '=', 'outgoing'), ('sequence_code', '=', 'OUT'), ('company_id', '=', self.container_id.project_id.company_id.id)], limit=1)

        vals = {
            'partner_id': self.partner_id.id,
            'location_id': self.container_id.location_id.id,
            'project_entry_id':self.container_id.project_id.id,
            'picking_type_id': picking_type.id,
            'move_type': 'direct',
            'location_dest_id': self.partner_id.property_stock_supplier.id,
            'move_ids_without_package': [],
            'sub_contract':True,
            'container_id': self.container_id.id
        }

        if self.container_id.sub_product_id.uom_id.uom_type == 'bigger':
            final_weight = self.container_id.net_gross_weight / self.container_id.sub_product_id.uom_id.factor_inv
        elif self.container_id.sub_product_id.uom_id.uom_type == 'smaller':
            final_weight = self.container_id.net_gross_weight * self.container_id.sub_product_id.uom_id.factor_inv
        else:
            final_weight = self.container_id.net_gross_weight

        list_items = []
        list_items.append((0, 0, {
            'product_id': self.container_id.sub_product_id.id,
            'product_uom_qty': final_weight,
            'reserved_availability': final_weight,
            'quantity_done': final_weight,
            'name': self.container_id.sub_product_id.name,
            'product_uom': self.container_id.sub_product_id.uom_id.id,
            'location_id': self.container_id.location_id.id,
            'location_dest_id':  self.partner_id.property_stock_supplier.id,
            'sub_container_ids': [(6, 0, self.container_id.ids)]
        }))
        vals['move_ids_without_package'] = list_items

        out_going_shipment = self.env["stock.picking"].create(vals)
        self.container_id.out_shipment_id = out_going_shipment.id

        in_vals = {
            'partner_id': self.partner_id.id,
            'location_id': self.partner_id.property_stock_supplier.id,
            'project_entry_id': self.container_id.project_id.id,
            'picking_type_id': picking_type_id.id,
            'move_type': 'direct',
            'location_dest_id': self.container_id.location_id.id,
            'move_ids_without_package': [],
            'sub_contract': True,
            'container_id': self.container_id.id,
        }
        incoming_shipment = self.env["stock.picking"].create(in_vals)
        self.container_id.in_shipment_id = incoming_shipment.id
        self.container_id.state = 'subcontract'
        return True


class POLine(models.TransientModel):
    _name = 'create.po.line'

    product_id = fields.Many2one("product.product", string="Product",required=True, domain="[('type', '=', 'service'),('purchase_ok', '=', True)]")
    qty = fields.Float("Quantity",default=1.0)
    price = fields.Float("Price",required=True)
    uom_id = fields.Many2one("uom.uom","UOM",required=True)
    wiz_id =  fields.Many2one("create.po")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id



