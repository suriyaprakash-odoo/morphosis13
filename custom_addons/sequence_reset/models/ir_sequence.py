from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    reset_weekly = fields.Boolean("Reset Weekly?")

    def reset_sequence_weekly(self):
        sequence_ids = self.search([('reset_weekly','=',True),('active','=',True)])
        day_number = datetime.today().weekday()
        for seq in sequence_ids:
            if day_number == 0:
                seq.number_next_actual = 1
        return True