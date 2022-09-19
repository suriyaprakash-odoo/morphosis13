from odoo import fields, models, api, _
from odoo.exceptions import UserError


class UpdateTimeReception(models.TransientModel):
    _name = 'update.reception.time'

    duration = fields.Float("Work Duration")

    def update_work_time(self):
        picking_obj = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking_obj:
            picking_obj.reception_manual_time = self.duration

        return {'type': 'ir.actions.act_window_close'} 