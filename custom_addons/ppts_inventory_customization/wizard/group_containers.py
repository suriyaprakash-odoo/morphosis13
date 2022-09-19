from odoo import fields, models, api, _
from odoo.exceptions import UserError

class GroupContainers(models.TransientModel):
    _name = 'group.container.wizard'

    @api.model
    def default_get(self, fields):
        res = super(GroupContainers, self).default_get(fields)
        picking = self.env['stock.picking'].browse(self.env.context.get('default_picking_id')).exists()
        if picking:
            res.update(
                lorry_entry_weight=picking.weight_at_entry,
                lorry_exit_weight=picking.weight_at_exit,
                container_weight= picking.weight_at_entry - picking.weight_at_exit,
            )
        return res

    lorry_entry_weight = fields.Float("Truck Weight at Entry(Kg)", digits=(12,4))
    lorry_exit_weight = fields.Float("Truck at Exit(Kg)", digits=(12,4))
    container_weight = fields.Float("Gross Weight(Kg)", digits=(12,4))
    tare_weight = fields.Float("Tare Weight(Kg)")
    project_id = fields.Many2one("project.container", string="Project", domain="[('status','in', ('reception','wip'))]")
    container_ids = fields.Many2many("project.container",string="Containers")
    project = fields.Many2one("project.entries",string="Project", domain="[('status','in', ('reception','wip'))]")
    picking_id = fields.Many2one("stock.picking", string="Picking ID")
    grouped_containers_weight = fields.Float('Grouped Containers Weight(Kg)', digits=(12,4))

    def action_group_containers(self):
        if self.container_ids:
            gross_weight = 0.0
            if self.container_weight and self.container_ids:
                gross_weight = self.grouped_containers_weight/len(self.container_ids)
            child_ids = []
            for cnt in self.container_ids:
                # gross_weight += cnt.gross_weight
                child_ids.append(cnt.id)
            parent_id = False
            for container in self.container_ids:
                if not parent_id:
                    vals = {
                        'project_id': container.project_id.id,
                        'internal_project_id' : container.internal_project_id.id,
                        'picking_id': container.picking_id.id,
                        'container_type_id': container.container_type_id.id,
                        'gross_weight' : self.grouped_containers_weight,
                        'quantity': container.quantity,
                        'content_type': container.content_type.id,
                        'main_product_id':container.main_product_id.id,
                        'sub_product_id':container.sub_product_id.id,
                        'action_type': container.action_type,
                        'confirmation':container.confirmation,
                        'location_id':container.location_id.id,
                        'returnable_container': container.returnable_container,
                        'child_container_ids':child_ids,
                        'second_process' : container.second_process,
                    }
                    print(vals,'--')
                    parent_id = self.env["project.container"].create(vals)

                container.is_child_container = True
                container.parent_container_id = parent_id
                container.gross_weight = container.gross_weight
                container.cnt_type = 'Child Containers'

            action = self.env.ref('ppts_inventory_customization.action_create_action_container').read()[0]
            action['views'] = [(self.env.ref('ppts_inventory_customization.project_container_form_view').id, 'form')]
            action['res_id'] = parent_id.id
            return action