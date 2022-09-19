from odoo import api, fields, models,_
from odoo.exceptions import UserError


class SecondProcessRC(models.TransientModel):
    _name = 'second.process.rc'

    action_type = fields.Selection([('grinding', 'Grinding'),
                                    ('dismantling', 'Dismantling'),
                                    ('repackaging', 'Repackaging'),
                                    ('sorting', 'Sorting'),
                                    ('vrac', 'Vrac'),
                                    ('test', 'Test')], string="Action Type")
    location_id = fields.Many2one("stock.location", string="Location",
                                  domain="[('usage','=','internal')]")
    container_ids = fields.Many2many("stock.container",string='Selected Containers')
    partner_id = fields.Many2one('res.partner',string="Client Name", domain="[('internal_company', '=', True)]")


    def action_second_process(self):
        self.env['internal.project'].create({
                'action_type' : self.action_type,
                'location_id' : self.location_id.id,
                'partner_id' : self.partner_id.id,
                'container_ids' : self.container_ids.ids
            })
        return {'type': 'ir.actions.act_window_close'}
    	# for rec in self.container_ids:
    	# 	self.env['project.container'].create({
    	# 			'second_process' : True,
    	# 			'partner_id' : self.partner_id.id,
    	# 			'container_type_id' : rec.container_type_id.id,
    	# 			'action_type' : self.action_type,
    	# 			'main_product_id' : rec.content_type_id.product_tmpl_id.id,
    	# 			'sub_product_id' : rec.content_type_id.id,
    	# 			'location_id' : self.location_id.id,
    	# 			'confirmation' : 'confirmed',
    	# 			'origin_container' : rec.id,
    	# 			'gross_weight' : rec.max_weight,
    	# 			'extra_tare' : rec.tare_weight,
    	# 		})
    	# # 	rec.state = 'second_process'
    	# return {'type': 'ir.actions.act_window_close'}