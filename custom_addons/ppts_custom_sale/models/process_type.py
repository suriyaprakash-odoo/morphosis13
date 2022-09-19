from odoo import fields, models, api, _

class ProcessType(models.Model):
	_name = "process.type"

	name = fields.Char('Process Name')
	estimated_production_cost = fields.Float('Esmitated Production Cost')