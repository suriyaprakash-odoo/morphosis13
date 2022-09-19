from odoo import api, fields, models,_
from datetime import timedelta, datetime
from odoo.exceptions import UserError


class CreateMoWizard(models.TransientModel):
    _name = 'create.mo.wizard'

    product_id = fields.Many2one("product.product", string="Product to Produce",domain="[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('type', 'in', ['product', 'consu'])]")
    quantity = fields.Float("Quantity to Produce", digits=(12, 4))
    bom_id = fields.Many2one("mrp.bom", string="Bill of Material",domain="""[
        '&',
                  '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""")
    uom_id = fields.Many2one("uom.uom", string="UOM")


    @api.onchange('product_id', 'picking_type_id')
    def onchange_product_id(self):
        """ Finds UoM of changed product. """
        if not self.product_id:
            self.bom_id = False
        else:
            bom = self.env['mrp.bom']._bom_find(product=self.product_id,bom_type='normal')
            if bom:
                self.bom_id = bom.id
                self.uom_id = self.bom_id.product_uom_id.id,
                self.quantity =  self.bom_id.product_qty


    def create_refining_mo(self):
        container = self.env['project.container'].browse(self.env.context.get('active_id'))

        vals = ({'default_product_id': self.product_id.id,'default_product_qty': self.quantity,
                 'default_bom_id': self.bom_id.id,'default_product_uom_id': self.uom_id.id,'default_project_id':container.project_id.id, 'default_container_id': container.id})
        return {
            'name': "Manufacturing Order",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'target': 'current',
            'context': vals,
        }
