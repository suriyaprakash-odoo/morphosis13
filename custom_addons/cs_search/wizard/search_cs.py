from odoo import fields, models, api, _
from datetime import timedelta, datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class SearchCS(models.TransientModel):
    _name = 'search.cs'

    cs_number = fields.Char('CS Number')
    int_project = fields.Many2one("internal.project",string="Internal Project")

    @api.onchange('cs_number')
    def onchange_cs_number(self):
        if self.cs_number:
            internal_project = self.env["internal.project"].search([('state','!=','done')])
            for line in internal_project:
                if line.container_ids:
                    for cnt in line.container_ids:
                        if cnt.name ==  self.cs_number:
                            self.int_project = line.id

    def search_and_open_containers(self):
        int_project = False

        if self.cs_number:
            internal_project = self.env["internal.project"].search([('state','!=','done')])
            for line in internal_project:
                if line.container_ids:
                    for cnt in line.container_ids:
                        if cnt.name ==  self.cs_number:
                            int_project = line.id

        if int_project:
            pr_containers = self.env["project.container"].search([('internal_project_id', '=', int_project)])
            if pr_containers:
                tree_id = self.env.ref('ppts_inventory_customization.project_container_tree_view').id
                form_id = self.env.ref('ppts_inventory_customization.project_container_form_view').id

                return {
                    'name': ('Project Container'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'tree,form',
                    'res_model': 'project.container',
                    'domain': [('internal_project_id', '=', self.int_project.id)],
                    'views': [(tree_id, 'tree'),(form_id, 'form')],
                    'target': 'current',
                }

            else:
                form_id = self.env.ref('internal_project.inernal_project_view_form').id
                return {
                    'name': ('Internal Project'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'tree,form',
                    'res_model': 'internal.project',
                    'res_id': self.int_project.id,
                    'views': [(form_id, 'form')],
                    'target': 'current',
                }

        else:
            raise UserError('This container is not mapped with any internal project!')