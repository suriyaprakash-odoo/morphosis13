from odoo import fields, models, api, _
from odoo.exceptions import UserError

    
class StockPickingInherit(models.Model):
    _inherit = "stock.picking"
    
    mobile_tree_wiz = fields.Many2one(comodel_name="custom.mobile.view.tree")


class ProjectContainerInherit(models.Model):
    _inherit = "project.container"
    
    mobile_tree_wiz = fields.Many2one(comodel_name="custom.mobile.view.tree")
    

class CustomTreeViewWizard(models.Model):
    _name = "custom.mobile.view.tree"
    
    name = fields.Char()
    
    stock_picking_ids = fields.One2many("stock.picking","mobile_tree_wiz")
    project_container_ids = fields.One2many("project.container","mobile_tree_wiz")
    
    is_stock_picking = fields.Boolean(default=False)
    is_project_container = fields.Boolean(default=False)
    
    
    def delete_mobile_tree_view(self):
        self.env['custom.mobile.view.tree'].sudo().search([]).unlink()
        