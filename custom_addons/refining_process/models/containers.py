from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class ProjectContainer(models.Model):
    _inherit = 'project.container'

    production_id = fields.Many2one("mrp.production", string="Manufacturing Order", readonly=1)
    refining_process = fields.Selection([('subcontract','Subcontract'),('mo','Manufacturing')])
    refining_container_id = fields.Many2one('refining.containers', string="Refining Container")
    state = fields.Selection(selection_add=[('manufacturing', 'Manufacturing')])
    is_refining = fields.Boolean("Is Refining")

    @api.onchange('project_id')
    def onchange_project_new(self):
        if self.project_id and self.project_id.project_type == 'refine':
            self.is_refining = True
        else:
            self.is_refining = False

    @api.onchange('refining_process')
    def onchange_refining_process(self):
        if self.refining_process and self.refining_process == 'subcontract':
            self.sub_contract = True
        else:
            self.sub_contract = False

    def action_create_mo(self):
        vals = ({'default_project_id':self.project_id.id, 'default_container_id': self.id})
        return {
            'name': "Manufacturing Order",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'target': 'current',
            'context': vals,
        }


    # def action_create_mo(self):
    #     return {
    #         'name': "Create Manufacturing Order",
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'create.mo.wizard',
    #         'target': 'new',
    #     }

    def action_open_mo(self):
        return {
            'name': "Manufacturing Order",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.production_id.id,
            'res_model': 'mrp.production',
            'target': 'current',
        }



class CreateContainers(models.TransientModel):
    _inherit = 'create.container.wizard'

    refining_container_id = fields.Many2one('refining.containers', string="Refining Container", domain="[('project_id','=',project_id)]")

    @api.onchange('refining_container_id')
    def onchange_refining_container_id(self):
        if self.refining_container_id:
            self.container_type_id = self.refining_container_id.container_type_id.id
            self.main_product_id = self.refining_container_id.product_id.product_tmpl_id.id
            self.sub_product_id = self.refining_container_id.product_id.id
            self.external_action_type = 'refining'
            self.gross_weight = self.refining_container_id.gross_weight

