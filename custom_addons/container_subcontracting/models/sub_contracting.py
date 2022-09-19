from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ProejctContainer(models.Model):
    _inherit = "project.container"

    sub_contract = fields.Boolean("Sub Contract?")

    sub_contract_po_id = fields.Many2one("purchase.order",string="Subcontract Purchase Order")
    in_shipment_id = fields.Many2one("stock.picking", string="Incoming Shipment")
    out_shipment_id = fields.Many2one("stock.picking", string="Outgoing Shipment")
    state = fields.Selection(selection_add=[('subcontract', 'Sub contract')])
    subcontract_rcvd = fields.Boolean("Subcontract Received")

    def create_subcontract_po(self):
        vals = ({'default_container_id':self.id})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.po',
            'target': 'new',
            'context': vals,
        }


class StockMove(models.Model):
    _inherit = "stock.move"

    sub_container_ids = fields.Many2many('project.container', string='Subcontract Containers')

class StockPicking(models.Model):
    _inherit = "stock.picking"

    sub_contract = fields.Boolean("Sub Contract Picking")
    container_id = fields.Many2one("project.container",string="Container")

    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        if self.sub_contract:
            container = self.env["project.container"].search([('in_shipment_id','=',self.id)])
            if container:
                container.subcontract_rcvd = True
                container.state = 'confirmed'
        return result


    def create_subcontract_fractions(self):
        return {
            'name': _('Container'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'project.container',
            'res_id': self.container_id.id,
            'views_id': False,
            'views': [(self.env.ref('ppts_inventory_customization.project_container_form_view').id or False, 'form')],
        }

