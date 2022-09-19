from odoo import fields, models, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one('project.entries',string='Project Entries')

    @api.model
    def create(self, vals):
    	res = super(AccountMove, self).create(vals)
    	if res.project_id:
    		self.env["project.account.move"].create({'account_id':res.id,'amount':res.amount_total,'untaxed_amount':res.amount_untaxed,'amount_residual':res.amount_residual,'project_id':res.project_id.id})
    	return res

    def write(self,vals):
        res = super(AccountMove, self).write(vals)
        if self.project_id:
            project_inv_obj = self.env['project.account.move'].search([('account_id' , '=' , self.id)])
            if project_inv_obj:
                project_inv_obj.amount = self.amount_total
                project_inv_obj.untaxed_amount = self.amount_untaxed
                project_inv_obj.amount_residual = self.amount_residual
        return res