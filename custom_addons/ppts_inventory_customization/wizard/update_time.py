from odoo import fields, models, api, _
from odoo.exceptions import UserError


class UpdateTime(models.TransientModel):
    _name = 'update.time'

    duration = fields.Float("Work Duration")

    def update_work_time(self):
        container = self.env['project.container'].browse(self.env.context.get('active_id'))
        if container:
            container.manual_time = self.duration