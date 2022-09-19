from odoo import fields, models, api, _
from odoo.exceptions import UserError

class UpdateStockContainerWeight(models.TransientModel):
    _name = 'update.stock.container.wizard'

    new_weight = fields.Float('New Net Weight')


    def update_weight(self):
    	container = self.env.context.get('active_id')
    	container_id = self.env['stock.container'].browse(container)

    	if container_id:
    		container_id.write({
				'net_weight_dup' : self.new_weight,
				})

    	return {'type': 'ir.actions.act_window_close'}